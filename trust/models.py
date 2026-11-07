"""Trust and safety: verified circles, guardians, ratings, notifications and the moderation log."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Circle(models.Model):
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=240, blank=True)
    members = models.ManyToManyField("accounts.UserProfile", related_name="circles", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class GuardianContact(models.Model):
    user = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE, related_name="guardians")
    guardian_name = models.CharField(max_length=80)
    guardian_phone = models.CharField(max_length=20)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.guardian_name} for {self.user}"


class Review(models.Model):
    ride = models.ForeignKey("rides.RidePost", on_delete=models.CASCADE, related_name="reviews")
    rater = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE, related_name="reviews_given")
    rated_user = models.ForeignKey(
        "accounts.UserProfile", on_delete=models.CASCADE, related_name="reviews_received"
    )
    score = models.PositiveSmallIntegerField()
    comment = models.CharField(max_length=400, blank=True)
    rater_weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["ride", "rater", "rated_user"], name="uniq_review_per_pair"
            ),
            models.CheckConstraint(
                condition=Q(score__gte=1) & Q(score__lte=5), name="review_score_1_to_5"
            ),
            models.CheckConstraint(
                condition=~Q(rater=F("rated_user")), name="review_not_self"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.rater} rated {self.rated_user}: {self.score}"


class Notification(models.Model):
    class Kind(models.TextChoices):
        INFO = "INFO", "Info"
        REQUEST = "REQUEST", "Request"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        GUARDIAN = "GUARDIAN", "Guardian"
        REVIEW = "REVIEW", "Review"

    user = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.INFO)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "is_read"], name="notif_user_read_idx")]

    def __str__(self) -> str:
        return self.message


class ModerationLog(models.Model):
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    target = models.CharField(max_length=160)
    action = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.action}: {self.target}"
