from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts import services as services_accounts
from accounts.decorators import profile_required, verified_required
from accounts.http import safe_next
from config.errors import RideError
from trust import services as trust_services
from trust.models import Review

from . import services
from .areas import AREAS
from .forms import RideForm, SearchForm
from .models import RidePost, RideRequest


def home(request):
    viewer = services_accounts.get_viewer(request)
    form = SearchForm(request.GET or None)
    filters = form.cleaned_data if form.is_bound and form.is_valid() else {}
    rides = services.search_rides(
        viewer,
        start=filters.get("start", "").strip(),
        end=filters.get("end", "").strip(),
        vehicle=filters.get("vehicle", ""),
        women_only=filters.get("women_only", False),
    )
    return render(request, "home.html", {
        "form": form,
        "rides": rides,
        "counts": services.site_counts(),
        "can_see_women_only": services.can_see_women_only(viewer),
    })


@verified_required
def ride_new(request):
    form = RideForm(request.POST or None, profile=request.profile)
    if request.method == "POST" and form.is_valid():
        ride = form.save(commit=False)
        ride.creator = request.profile
        ride.status = RidePost.Status.OPEN
        ride.save()
        messages.success(request, "Your ride is live.")
        return redirect(ride)
    return render(request, "ride_form.html", {"form": form, "areas": AREAS})


def ride_detail(request, pk):
    ride = get_object_or_404(RidePost.objects.select_related("creator__user"), pk=pk)
    viewer = services_accounts.get_viewer(request)
    if not services.can_view_ride(viewer, ride):
        raise Http404  # do not reveal that a women-only ride exists
    is_host = viewer is not None and ride.creator_id == viewer.pk
    my_request = None
    if viewer is not None and not is_host:
        my_request = RideRequest.objects.filter(ride=ride, requester=viewer).first()
    pending = []
    if is_host:
        pending = list(
            RideRequest.objects.filter(ride=ride, status=RideRequest.Status.PENDING)
            .select_related("requester__user")
        )
    review_targets = []
    partners = []
    if viewer is not None and ride.status in (
        RidePost.Status.OPEN, RidePost.Status.FILLED, RidePost.Status.COMPLETED
    ):
        people = services.ride_participants(ride)
        if viewer.pk in {p.pk for p in people}:
            reviewed = set(
                Review.objects.filter(ride=ride, rater=viewer).values_list("rated_user_id", flat=True)
            )
            partners = [
                {"profile": p, "rated": p.pk in reviewed}
                for p in people if p.pk != viewer.pk
            ]
            if ride.status == RidePost.Status.COMPLETED:
                review_targets = [item["profile"] for item in partners if not item["rated"]]
    return render(request, "ride_detail.html", {
        "ride": ride,
        "is_host": is_host,
        "my_request": my_request,
        "pending_requests": pending,
        "contacts": services.ride_contacts(viewer, ride),
        "review_targets": review_targets,
        "partners": partners,
        "can_request": viewer is not None and not is_host and ride.is_bookable
        and (my_request is None or my_request.status == RideRequest.Status.CANCELLED),
    })


def _run_ride_action(request, action, *args, success: str, fallback_ride_id: int):
    try:
        action(*args)
        messages.success(request, success)
    except RideError as exc:
        messages.error(request, str(exc))
    return redirect(safe_next(request, reverse("rides:ride_detail", args=[fallback_ride_id])))


@require_POST
@verified_required
def ride_request(request, pk):
    ride = get_object_or_404(RidePost, pk=pk)
    if not services.can_view_ride(request.profile, ride):
        raise Http404
    try:
        services.send_request(ride, request.profile)
        messages.success(request, "Request sent. The host will be notified.")
    except RideError as exc:
        messages.error(request, str(exc))
    return redirect(ride)


def _decide(request, pk, accept: bool):
    ride_request_obj = get_object_or_404(RideRequest, pk=pk)
    return _run_ride_action(
        request, services.decide_request, pk, request.profile, accept,
        success="Request accepted." if accept else "Request declined.",
        fallback_ride_id=ride_request_obj.ride_id,
    )


@require_POST
@profile_required
def request_accept(request, pk):
    return _decide(request, pk, True)


@require_POST
@profile_required
def request_reject(request, pk):
    return _decide(request, pk, False)


@require_POST
@profile_required
def request_cancel(request, pk):
    ride_request_obj = get_object_or_404(RideRequest, pk=pk)
    return _run_ride_action(
        request, services.cancel_request, pk, request.profile,
        success="Request cancelled.", fallback_ride_id=ride_request_obj.ride_id,
    )


@require_POST
@profile_required
def ride_complete(request, pk):
    get_object_or_404(RidePost, pk=pk)
    return _run_ride_action(
        request, services.complete_ride, pk, request.profile,
        success="Ride marked complete. Riders were asked to review.", fallback_ride_id=pk,
    )


@require_POST
@profile_required
def ride_cancel(request, pk):
    get_object_or_404(RidePost, pk=pk)
    return _run_ride_action(
        request, services.cancel_ride, pk, request.profile,
        success="Ride cancelled and riders notified.", fallback_ride_id=pk,
    )


@profile_required
def dashboard(request):
    profile = request.profile
    my_rides = RidePost.objects.filter(creator=profile).order_by("-departure_time")[:20]
    my_requests = (
        RideRequest.objects.filter(requester=profile)
        .select_related("ride__creator__user").order_by("-created_at")[:20]
    )
    incoming = (
        RideRequest.objects.filter(ride__creator=profile, status=RideRequest.Status.PENDING)
        .select_related("ride", "requester__user")
    )
    completed = (
        RidePost.objects.filter(creator=profile, status=RidePost.Status.COMPLETED).count()
        + RideRequest.objects.filter(
            requester=profile, status=RideRequest.Status.ACCEPTED,
            ride__status=RidePost.Status.COMPLETED,
        ).count()
    )
    return render(request, "dashboard.html", {
        "to_rate": trust_services.pending_reviews(profile),
        "my_rides": my_rides,
        "my_requests": my_requests,
        "incoming": incoming,
        "counts": {
            "rides": RidePost.objects.filter(creator=profile).count(),
            "requests": RideRequest.objects.filter(requester=profile).count(),
            "completed": completed,
        },
    })
