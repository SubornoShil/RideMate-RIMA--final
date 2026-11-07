"""Small request helpers used by more than one app."""
from django.utils.http import url_has_allowed_host_and_scheme


def client_ip(request) -> str:
    # REMOTE_ADDR only: X-Forwarded-For can be forged by the client.
    return request.META.get("REMOTE_ADDR", "")


def safe_next(request, fallback: str) -> str:
    target = request.POST.get("next") or request.GET.get("next") or ""
    allowed = url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )
    return target if allowed else fallback
