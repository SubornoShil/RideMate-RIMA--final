from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import profile_required
from accounts.models import UserProfile
from config.errors import RideError
from rides.models import RidePost, RideRequest

from . import services
from .forms import CircleJoinForm, GuardianForm, ReviewForm
from .models import Circle, GuardianContact, Notification, Review


@profile_required
def review_new(request, pk, profile_id):
    ride = get_object_or_404(RidePost.objects.select_related("creator__user"), pk=pk)
    target = get_object_or_404(UserProfile.objects.select_related("user"), pk=profile_id)
    problem = services.review_problem(ride, request.profile, target)
    if problem:
        messages.error(request, problem)
        return redirect(ride)
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.submit_review(
                ride, request.profile, target, form.cleaned_data["score"],
                form.cleaned_data["comment"],
            )
            messages.success(request, "Thanks. Your review was recorded.")
            return redirect(ride)
        except RideError as exc:
            messages.error(request, str(exc))
    return render(request, "review_form.html", {"form": form, "ride": ride, "target": target})


def _profile_page(request, guardian_form):
    profile = request.profile
    return render(request, "profile.html", {
        "guardian_form": guardian_form,
        "guardians": profile.guardians.all(),
        "circles": profile.circles.all(),
        "reviews": profile.reviews_received.select_related("rater__user")[:10],
        "guardian_limit": services.MAX_GUARDIANS,
    })


@profile_required
def profile(request):
    return _profile_page(request, GuardianForm())


@require_POST
@profile_required
def guardian_add(request):
    form = GuardianForm(request.POST)
    if form.is_valid():
        try:
            services.add_guardian(
                request.profile, form.cleaned_data["guardian_name"],
                form.cleaned_data["guardian_phone"],
            )
            messages.success(request, "Guardian added.")
            return redirect("trust:profile")
        except RideError as exc:
            messages.error(request, str(exc))
            return redirect("trust:profile")
    return _profile_page(request, form)


@require_POST
@profile_required
def guardian_delete(request, pk):
    guardian = get_object_or_404(GuardianContact, pk=pk, user=request.profile)
    guardian.delete()
    messages.success(request, "Guardian removed.")
    return redirect("trust:profile")


@profile_required
def notifications(request):
    items = list(Notification.objects.filter(user=request.profile)[:50])
    Notification.objects.filter(user=request.profile, is_read=False).update(is_read=True)
    return render(request, "notifications.html", {"items": items})


@profile_required
def analytics(request):
    if not request.user.is_staff:
        raise PermissionDenied
    rides = RidePost.objects.all()
    total_rides = rides.count()
    by_vehicle = []
    for row in rides.values("vehicle_type").annotate(n=Count("id")).order_by("-n"):
        label = RidePost.Vehicle(row["vehicle_type"]).label
        share = round(row["n"] * 100 / total_rides, 1) if total_rides else 0
        by_vehicle.append({"label": label, "count": row["n"], "share": share})
    return render(request, "analytics.html", {
        "totals": {
            "users": UserProfile.objects.count(),
            "rides": total_rides,
            "completed": rides.filter(status=RidePost.Status.COMPLETED).count(),
            "open": rides.filter(status=RidePost.Status.OPEN).count(),
            "requests": RideRequest.objects.count(),
            "accepted": RideRequest.objects.filter(status=RideRequest.Status.ACCEPTED).count(),
            "women_only": rides.filter(female_only=True).count(),
            "reviews": Review.objects.count(),
        },
        "by_vehicle": by_vehicle,
        "top_routes": rides.values("start_location", "end_location")
        .annotate(n=Count("id")).order_by("-n", "start_location")[:6],
    })


@profile_required
def circles(request):
    mine = request.profile.circles.annotate(member_count=Count("members"))
    return render(request, "circles.html", {"circles": mine, "form": CircleJoinForm()})


@require_POST
@profile_required
def circle_join(request):
    form = CircleJoinForm(request.POST)
    if form.is_valid():
        try:
            circle = services.join_circle(request.profile, form.cleaned_data["code"])
            messages.success(request, f"You joined {circle.name}.")
        except RideError as exc:
            messages.error(request, str(exc))
    else:
        messages.error(request, "Enter a circle code.")
    return redirect("trust:circles")


@require_POST
@profile_required
def circle_leave(request, pk):
    circle = get_object_or_404(Circle, pk=pk, members=request.profile)
    circle.members.remove(request.profile)
    messages.success(request, f"You left {circle.name}.")
    return redirect("trust:circles")
