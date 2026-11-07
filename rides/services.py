"""Ride rules: search, visibility, the request flow, completing and cancelling."""
from functools import partial

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.utils import timezone

from accounts.models import UserProfile
from config.errors import RideError
from trust.models import Circle, Notification
from trust.services import notify, send_guardian_alerts

from .models import RidePost, RideRequest
from .utils import ride_link, ride_participants, ride_when

SEARCH_LIMIT = 60


def can_see_women_only(profile: UserProfile | None) -> bool:
    return profile is not None and profile.gender == UserProfile.Gender.FEMALE


def can_view_ride(profile: UserProfile | None, ride: RidePost) -> bool:
    return not ride.female_only or can_see_women_only(profile)


def search_rides(viewer, start="", end="", vehicle="", women_only=False):
    queryset = RidePost.objects.filter(
        status=RidePost.Status.OPEN, available_seats__gt=0, departure_time__gt=timezone.now()
    ).select_related("creator__user")
    if start:
        queryset = queryset.filter(start_location__icontains=start)
    if end:
        queryset = queryset.filter(end_location__icontains=end)
    if vehicle in RidePost.Vehicle.values:
        queryset = queryset.filter(vehicle_type=vehicle)
    if not can_see_women_only(viewer):
        queryset = queryset.filter(female_only=False)
    elif women_only:
        queryset = queryset.filter(female_only=True)

    if viewer is None:
        queryset = queryset.annotate(in_circle=Value(False, output_field=BooleanField()))
    else:
        shared = Circle.objects.filter(members=OuterRef("creator")).filter(members=viewer)
        queryset = queryset.annotate(in_circle=Exists(shared))
    return list(queryset.order_by("-in_circle", "departure_time")[:SEARCH_LIMIT])


def site_counts() -> dict:
    return {
        "members": UserProfile.objects.count(),
        "upcoming": RidePost.objects.filter(
            status=RidePost.Status.OPEN, departure_time__gt=timezone.now()
        ).count(),
        "completed": RidePost.objects.filter(status=RidePost.Status.COMPLETED).count(),
    }


def ride_contacts(viewer: UserProfile | None, ride: RidePost) -> list[dict]:
    """Phone numbers, only for the host and accepted riders of this ride."""
    if viewer is None:
        return []
    people = ride_participants(ride)
    if viewer.pk not in {p.pk for p in people}:
        return []
    return [
        {
            "name": p.display_name,
            "phone": p.phone_number,
            "role": "Host" if p.pk == ride.creator_id else "Rider",
        }
        for p in people
        if p.pk != viewer.pk
    ]


def send_request(ride: RidePost, profile: UserProfile) -> RideRequest:
    if not profile.is_verified:
        raise RideError("Verify your phone number before sending requests.")
    if ride.creator_id == profile.pk:
        raise RideError("You cannot request your own ride.")
    if ride.female_only and profile.gender != UserProfile.Gender.FEMALE:
        raise RideError("This ride is for women only.")
    if not ride.is_bookable:
        raise RideError("This ride is no longer open for requests.")
    existing = RideRequest.objects.filter(ride=ride, requester=profile).first()
    try:
        with transaction.atomic():
            if existing is None:
                ride_request = RideRequest.objects.create(ride=ride, requester=profile)
            elif existing.status == RideRequest.Status.CANCELLED:
                existing.status = RideRequest.Status.PENDING
                existing.save(update_fields=["status"])
                ride_request = existing
            else:
                raise RideError("You already have a request on this ride.")
    except IntegrityError as exc:
        raise RideError("You already have a request on this ride.") from exc
    notify(
        ride.creator,
        f"{profile.display_name} asked to join {ride}.",
        Notification.Kind.REQUEST,
        ride_link(ride),
    )
    return ride_request


@transaction.atomic
def decide_request(request_id: int, host: UserProfile, accept: bool) -> RideRequest:
    ride_id = RideRequest.objects.values_list("ride_id", flat=True).get(pk=request_id)
    ride = RidePost.objects.select_for_update().get(pk=ride_id)
    ride_request = RideRequest.objects.select_for_update().get(pk=request_id)
    if ride.creator_id != host.pk:
        raise PermissionDenied
    if ride_request.status != RideRequest.Status.PENDING:
        raise RideError("This request has already been handled.")
    rider = ride_request.requester
    if accept:
        if ride.status != RidePost.Status.OPEN or ride.available_seats < 1:
            raise RideError("There are no seats left on this ride.")
        ride.available_seats -= 1
        if ride.available_seats == 0:
            ride.status = RidePost.Status.FILLED
        ride.save(update_fields=["available_seats", "status"])
        ride_request.status = RideRequest.Status.ACCEPTED
        notify(
            rider, f"You are in: {ride} on {ride_when(ride)}.", Notification.Kind.ACCEPTED, ride_link(ride)
        )
        transaction.on_commit(partial(send_guardian_alerts, ride, [rider, host]))
    else:
        ride_request.status = RideRequest.Status.REJECTED
        notify(
            rider, f"Your request for {ride} was declined.", Notification.Kind.REJECTED, ride_link(ride)
        )
    ride_request.save(update_fields=["status"])
    return ride_request


@transaction.atomic
def cancel_request(request_id: int, rider: UserProfile) -> RideRequest:
    ride_id = RideRequest.objects.values_list("ride_id", flat=True).get(pk=request_id)
    ride = RidePost.objects.select_for_update().get(pk=ride_id)
    ride_request = RideRequest.objects.select_for_update().get(pk=request_id)
    if ride_request.requester_id != rider.pk:
        raise PermissionDenied
    if ride_request.status not in (RideRequest.Status.PENDING, RideRequest.Status.ACCEPTED):
        raise RideError("This request can no longer be cancelled.")
    if ride.status in (RidePost.Status.COMPLETED, RidePost.Status.CANCELLED):
        raise RideError("This ride is already closed.")
    if ride_request.status == RideRequest.Status.ACCEPTED:
        ride.available_seats += 1
        if ride.status == RidePost.Status.FILLED:
            ride.status = RidePost.Status.OPEN
        ride.save(update_fields=["available_seats", "status"])
    ride_request.status = RideRequest.Status.CANCELLED
    ride_request.save(update_fields=["status"])
    notify(
        ride.creator,
        f"{rider.display_name} cancelled their seat on {ride}.",
        Notification.Kind.INFO,
        ride_link(ride),
    )
    return ride_request


@transaction.atomic
def complete_ride(ride_id: int, host: UserProfile) -> RidePost:
    ride = RidePost.objects.select_for_update().get(pk=ride_id)
    if ride.creator_id != host.pk:
        raise PermissionDenied
    if ride.status not in (RidePost.Status.OPEN, RidePost.Status.FILLED):
        raise RideError("This ride is already closed.")
    ride.status = RidePost.Status.COMPLETED
    ride.save(update_fields=["status"])
    RideRequest.objects.filter(ride=ride, status=RideRequest.Status.PENDING).update(
        status=RideRequest.Status.CANCELLED
    )
    for rider in ride_participants(ride)[1:]:
        notify(
            rider,
            f"{ride} is complete. Rate the people you rode with.",
            Notification.Kind.REVIEW,
            ride_link(ride),
        )
    return ride


def _cancel_ride_locked(ride: RidePost) -> None:
    ride.status = RidePost.Status.CANCELLED
    ride.save(update_fields=["status"])
    affected = list(
        RideRequest.objects.filter(
            ride=ride, status__in=[RideRequest.Status.PENDING, RideRequest.Status.ACCEPTED]
        ).select_related("requester")
    )
    RideRequest.objects.filter(pk__in=[r.pk for r in affected]).update(
        status=RideRequest.Status.CANCELLED
    )
    for ride_request in affected:
        notify(
            ride_request.requester,
            f"{ride} on {ride_when(ride)} was cancelled.",
            Notification.Kind.INFO,
            ride_link(ride),
        )


@transaction.atomic
def cancel_ride(ride_id: int, host: UserProfile) -> RidePost:
    ride = RidePost.objects.select_for_update().get(pk=ride_id)
    if ride.creator_id != host.pk:
        raise PermissionDenied
    if ride.status not in (RidePost.Status.OPEN, RidePost.Status.FILLED):
        raise RideError("This ride is already closed.")
    _cancel_ride_locked(ride)
    return ride


@transaction.atomic
def moderator_cancel_ride(ride_id: int) -> bool:
    ride = RidePost.objects.select_for_update().get(pk=ride_id)
    if ride.status not in (RidePost.Status.OPEN, RidePost.Status.FILLED):
        return False
    _cancel_ride_locked(ride)
    return True
