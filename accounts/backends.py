from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class IdentifierBackend(ModelBackend):
    """Log in with a username or an email address, case-insensitively."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or "").strip()
        user_model = get_user_model()
        user = (
            user_model.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
            .order_by("pk")
            .first()
            if identifier
            else None
        )
        if user is None:
            # Burn the same hashing time so response timing does not reveal accounts.
            user_model().set_password(password or "")
            return None
        if user.check_password(password or "") and self.user_can_authenticate(user):
            return user
        return None
