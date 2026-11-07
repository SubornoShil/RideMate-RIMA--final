from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .services import get_profile


def profile_required(view):
    """Require login and attach the member's profile as request.profile."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        request.profile = get_profile(request.user)
        return view(request, *args, **kwargs)

    return login_required(wrapper)


def verified_required(view):
    """Like profile_required, and the phone number must be verified."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.profile.is_verified:
            messages.warning(request, "Verify your phone number to do that.")
            return redirect("accounts:verify_phone")
        return view(request, *args, **kwargs)

    return profile_required(wrapper)
