"""Trust and safety rules: notifications, guardian alerts, ratings and the trust score."""
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.urls import reverse

from accounts.models import UserProfile
from accounts.sms import send_sms
from config.errors import RideError
from rides.models import RidePost, RideRequest
from rides.utils import ride_link, ride_participants, ride_when

from .models import Circle, GuardianContact, ModerationLog, Notification, Review

MAX_GUARDIANS = 3
NEW_ACCOUNT_REVIEW_WEIGHT = 0.5


def recalculate_trust(profile: UserProfile) -> float:
    """Weighted average of the ratings a member received, scaled to 0-100."""
    rows = list(profile.reviews_received.values_list("score", "rater_weight"))
    total_weight = sum(weight for _, weight in rows)
    if total_weight:
        average = sum(score * weight for score, weight in rows) / total_weight
        profile.trust_score = round(average * 20, 1)
    else:
        profile.trust_score = 100
    profile.save(update_fields=["trust_score"])
    return profile.trust_score


def log_moderation(moderator, target: str, action: str) -> ModerationLog:
    return ModerationLog.objects.create(moderator=moderator, target=target, action=action)


def notify(profile, message, kind=Notification.Kind.INFO, link="") -> Notification:
    return Notification.objects.create(user=profile, message=message[:255], kind=kind, link=link)


def send_guardian_alerts(ride: RidePost, members: list[UserProfile]) -> None:
    for member in members:
        guardians = list(member.guardians.all())
        if not guardians:
            continue
        text = (
            f"{member.display_name} is sharing a ride from {ride.start_location} to "
            f"{ride.end_location}, leaving {ride_when(ride)}. Sent by RideMate Guardian Mode."
        )
        sent = sum(1 for g in guardians if send_sms(g.guardian_phone, text))
        notify(
            member,
            f"Guardian alert sent to {sent} of {len(guardians)} contact(s).",
            Notification.Kind.GUARDIAN,
            ride_link(ride),
        )


@transaction.atomic
def add_guardian(profile: UserProfile, name: str, phone: str) -> GuardianContact:
    UserProfile.objects.select_for_update().get(pk=profile.pk)
    if GuardianContact.objects.filter(user=profile).count() >= MAX_GUARDIANS:
        raise RideError(f"You can add up to {MAX_GUARDIANS} guardians.")
    return GuardianContact.objects.create(user=profile, guardian_name=name, guardian_phone=phone)


def review_problem(ride: RidePost, rater: UserProfile, target: UserProfile) -> str | None:
    if ride.status != RidePost.Status.COMPLETED:
        return "Reviews open once the ride is completed."
    if rater.pk == target.pk:
        return "You cannot review yourself."
    ids = {p.pk for p in ride_participants(ride)}
    if rater.pk not in ids or target.pk not in ids:
        return "Only people who shared this ride can review each other."
    if Review.objects.filter(ride=ride, rater=rater, rated_user=target).exists():
        return "You already reviewed this person for this ride."
    return None


def pending_reviews(profile: UserProfile, limit: int = 10) -> list[dict]:
    """Completed rides this person shared where someone is still waiting for a rating."""
    rides = (
        RidePost.objects.filter(status=RidePost.Status.COMPLETED)
        .filter(Q(creator=profile) | Q(requests__requester=profile, requests__status=RideRequest.Status.ACCEPTED))
        .select_related("creator__user").distinct().order_by("-departure_time")[:limit]
    )
    out = []
    for ride in rides:
        done = set(
            Review.objects.filter(ride=ride, rater=profile).values_list("rated_user_id", flat=True)
        )
        todo = [p for p in ride_participants(ride) if p.pk != profile.pk and p.pk not in done]
        if todo:
            out.append({"ride": ride, "people": todo})
    return out


@transaction.atomic
def submit_review(ride, rater, target, score: int, comment: str = "") -> Review:
    problem = review_problem(ride, rater, target)
    if problem:
        raise RideError(problem)
    weight = NEW_ACCOUNT_REVIEW_WEIGHT if rater.is_new_account else 1.0
    try:
        review = Review.objects.create(
            ride=ride, rater=rater, rated_user=target, score=score,
            comment=comment.strip(), rater_weight=weight,
        )
    except IntegrityError as exc:
        raise RideError("You already reviewed this person for this ride.") from exc
    recalculate_trust(target)
    notify(
        target,
        f"{rater.display_name} left you a {score}-star review.",
        Notification.Kind.REVIEW,
        reverse("trust:profile"),
    )
    return review


def join_circle(profile: UserProfile, code: str) -> Circle:
    circle = Circle.objects.filter(code__iexact=code.strip()).first()
    if circle is None:
        raise RideError("No circle uses that code.")
    circle.members.add(profile)
    return circle
