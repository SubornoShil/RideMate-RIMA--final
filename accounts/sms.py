"""Pluggable SMS sending. send_sms never raises and returns True or False."""
import base64
import json
import logging
import urllib.parse
import urllib.request
from http.client import HTTPException

from django.conf import settings

from .phone import to_e164

logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 8


def _console(to: str, message: str) -> bool:
    # Development only: this is the one place a code may appear in logs.
    logger.info("[sms:console] to=%s message=%s", to, message)
    return True


def _twilio(to: str, message: str) -> bool:
    sid, token = settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
    if not (sid and token and settings.TWILIO_FROM_NUMBER):
        logger.error("Twilio SMS backend selected but credentials are missing.")
        return False
    body = urllib.parse.urlencode(
        {"To": to_e164(to), "From": settings.TWILIO_FROM_NUMBER, "Body": message}
    ).encode()
    request = urllib.request.Request(  # noqa: S310 - fixed https URL
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=body
    )
    credentials = base64.b64encode(f"{sid}:{token}".encode()).decode()
    request.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
        return 200 <= response.status < 300


def _http(to: str, message: str) -> bool:
    if not settings.SMS_HTTP_URL.startswith("https://"):
        logger.error("SMS_HTTP_URL must be an https:// URL.")
        return False
    payload = json.dumps(
        {"to": to_e164(to), "message": message, "sender": settings.SMS_HTTP_SENDER}
    ).encode()
    request = urllib.request.Request(  # noqa: S310 - scheme checked above
        settings.SMS_HTTP_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    if settings.SMS_HTTP_TOKEN:
        request.add_header("Authorization", f"Bearer {settings.SMS_HTTP_TOKEN}")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
        return 200 <= response.status < 300


BACKENDS = {"console": _console, "twilio": _twilio, "http": _http}


def send_sms(to: str, message: str) -> bool:
    sender = BACKENDS.get(settings.SMS_BACKEND)
    if sender is None:
        logger.error("Unknown SMS_BACKEND %r.", settings.SMS_BACKEND)
        return False
    try:
        return bool(sender(to, message))
    except (OSError, ValueError, HTTPException):
        # Details are omitted on purpose: the message may contain a login code.
        logger.exception("SMS delivery failed via %s backend.", settings.SMS_BACKEND)
        return False
