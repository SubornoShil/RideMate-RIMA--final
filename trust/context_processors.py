import logging

from django.db import DatabaseError

from accounts.services import get_profile

logger = logging.getLogger(__name__)


def unread(request):
    """Number of unread notifications, shown as a badge in the navigation bar."""
    count = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        try:
            count = get_profile(user).notifications.filter(is_read=False).count()
        except DatabaseError:
            logger.warning("Could not count notifications.", exc_info=True)
    return {"unread_count": count}
