import secrets

from django.conf import settings


def build_csp(nonce: str) -> str:
    script = ["'self'", f"'nonce-{nonce}'"]
    style = ["'self'", f"'nonce-{nonce}'", "https://fonts.googleapis.com"]
    img = ["'self'", "data:"]
    connect = ["'self'"]
    parts = {}
    if settings.GOOGLE_MAPS_API_KEY:
        script.append("https://maps.googleapis.com")
        connect.append("https://maps.googleapis.com")
        img += ["https://maps.gstatic.com", "https://maps.googleapis.com"]
        parts["style-src-attr"] = ["'unsafe-inline'"]
    if settings.PLAUSIBLE_DOMAIN:
        script.append("https://plausible.io")
        connect.append("https://plausible.io")
    policy = {
        "default-src": ["'self'"],
        "script-src": script,
        "style-src": style,
        "img-src": img,
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "connect-src": connect,
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "object-src": ["'none'"],
        **parts,
    }
    return "; ".join(f"{key} {' '.join(values)}" for key, values in policy.items())


class SecurityHeadersMiddleware:
    """Per-request CSP nonce plus Permissions-Policy.

    The admin is left on Django's own markup, which uses inline styles, and DEBUG
    error pages use inline scripts, so neither gets the strict policy.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self), payment=()"
        admin_prefix = "/" + settings.ADMIN_URL
        if not settings.DEBUG and not request.path.startswith(admin_prefix):
            response["Content-Security-Policy"] = build_csp(request.csp_nonce)
        return response
