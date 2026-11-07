import logging

from django.conf import settings
from django.db import DatabaseError

from .services import get_profile

logger = logging.getLogger(__name__)


def site(request):
    """Site-wide template variables, plus the signed-in member for the navigation bar."""
    context = {
        "csp_nonce": getattr(request, "csp_nonce", ""),
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
        "PLAUSIBLE_DOMAIN": settings.PLAUSIBLE_DOMAIN,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "nav_profile": None,
        "email_unconfirmed": False,
    }
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        try:
            profile = get_profile(user)
            context["nav_profile"] = profile
            context["email_unconfirmed"] = not profile.email_verified
        except DatabaseError:
            logger.warning("Could not load navigation context.", exc_info=True)
    return context
