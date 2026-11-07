"""Small ride helpers shared with the trust app (kept free of other imports to avoid cycles)."""
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile

from .models import RidePost, RideRequest


def ride_link(ride) -> str:
    return reverse("rides:ride_detail", args=[ride.pk])


def ride_when(ride) -> str:
    return timezone.localtime(ride.departure_time).strftime("%a %d %b, %I:%M %p")


def ride_participants(ride: RidePost) -> list[UserProfile]:
    riders = [
        r.requester
        for r in RideRequest.objects.filter(ride=ride, status=RideRequest.Status.ACCEPTED)
        .select_related("requester__user")
        .order_by("id")
    ]
    return [ride.creator, *riders]
