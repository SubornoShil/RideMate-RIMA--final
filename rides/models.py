"""Rides: a trip someone posts, and the requests riders make to join it."""
from urllib.parse import urlencode

from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone


class RidePost(models.Model):
    class Vehicle(models.TextChoices):
        CNG = "CNG", "CNG"
        RICKSHAW = "RICKSHAW", "Rickshaw"
        BIKE = "BIKE", "Bike"
        CAR = "CAR", "Car"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        FILLED = "FILLED", "Filled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    creator = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE, related_name="rides")
    start_location = models.CharField(max_length=120)
    end_location = models.CharField(max_length=120)
    start_latitude = models.FloatField(null=True, blank=True)
    start_longitude = models.FloatField(null=True, blank=True)
    end_latitude = models.FloatField(null=True, blank=True)
    end_longitude = models.FloatField(null=True, blank=True)
    departure_time = models.DateTimeField()
    vehicle_type = models.CharField(max_length=10, choices=Vehicle.choices, default=Vehicle.CNG)
    female_only = models.BooleanField(default=False)
    available_seats = models.PositiveSmallIntegerField(validators=[MaxValueValidator(6)])
    fare_per_seat = models.PositiveIntegerField("fare per seat (taka)", default=0)
    note = models.CharField(max_length=300, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["departure_time"]
        indexes = [
            models.Index(fields=["status", "departure_time"], name="ride_status_departure_idx"),
            models.Index(fields=["start_location"], name="ride_start_idx"),
            models.Index(fields=["end_location"], name="ride_end_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(available_seats__lte=6), name="ride_seats_max_six"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.start_location} to {self.end_location}"

    def get_absolute_url(self) -> str:
        return reverse("rides:ride_detail", args=[self.pk])

    @property
    def is_bookable(self) -> bool:
        return (
            self.status == self.Status.OPEN
            and self.available_seats > 0
            and self.departure_time > timezone.now()
        )

    @property
    def vehicle_icon(self) -> str:
        """Key the templates use to pick an inline SVG glyph."""
        return self.vehicle_type.lower()

    @property
    def maps_url(self) -> str:
        def point(name: str, lat: float | None, lng: float | None) -> str:
            if lat is not None and lng is not None:
                return f"{lat},{lng}"
            return f"{name}, Bangladesh"

        query = urlencode(
            {
                "api": 1,
                "origin": point(self.start_location, self.start_latitude, self.start_longitude),
                "destination": point(self.end_location, self.end_latitude, self.end_longitude),
                "travelmode": "driving",
            }
        )
        return f"https://www.google.com/maps/dir/?{query}"


class RideRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    ride = models.ForeignKey(RidePost, on_delete=models.CASCADE, related_name="requests")
    requester = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE, related_name="requests")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["ride", "requester"], name="uniq_request_per_ride"),
        ]

    def __str__(self) -> str:
        return f"{self.requester} -> {self.ride} ({self.status})"
