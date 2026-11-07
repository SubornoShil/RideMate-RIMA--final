"""Identity: who a member is (profile, phone, gender, verification)."""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

NEW_ACCOUNT_DAYS = 7


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    phone_number = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.OTHER)
    trust_score = models.FloatField(default=100)
    is_verified = models.BooleanField("phone verified", default=False)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        return self.user.get_full_name() or self.user.username

    @property
    def initials(self) -> str:
        parts = self.display_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.display_name[:2].upper()

    @property
    def is_new_account(self) -> bool:
        return timezone.now() - self.created_at < timedelta(days=NEW_ACCOUNT_DAYS)

    @property
    def trust_label(self) -> str:
        if self.trust_score >= 90:
            return "Excellent"
        if self.trust_score >= 75:
            return "Good"
        if self.trust_score >= 60:
            return "Fair"
        return "Low"

    def recalculate_trust(self) -> float:
        """The score itself is stored here; the maths lives in the trust app."""
        from trust.services import recalculate_trust  # imported late: trust depends on accounts

        return recalculate_trust(self)
