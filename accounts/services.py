"""Identity rules: profiles, login lockout, phone codes and email confirmation."""
import enum
import logging
import secrets
import time
from smtplib import SMTPException

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import constant_time_compare, salted_hmac

from .models import UserProfile
from .sms import send_sms

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 600
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60
LOGIN_MAX_FAILURES = 5
LOGIN_LOCK_SECONDS = 15 * 60
EMAIL_TOKEN_SECONDS = 2 * 24 * 60 * 60
EMAIL_SALT = "accounts.verify-email"


def get_profile(user) -> UserProfile:
    """Return the profile, creating one for accounts made with createsuperuser."""
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(
            user=user, phone_number=f"staff{user.pk}", gender=UserProfile.Gender.OTHER
        )


def _lock_key(identifier: str, ip: str) -> str:
    return f"login-fail:{identifier.strip().lower()}:{ip}"


def is_login_locked(identifier: str, ip: str) -> bool:
    return cache.get(_lock_key(identifier, ip), 0) >= LOGIN_MAX_FAILURES


def register_login_failure(identifier: str, ip: str) -> None:
    key = _lock_key(identifier, ip)
    cache.add(key, 0, LOGIN_LOCK_SECONDS)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, LOGIN_LOCK_SECONDS)


def clear_login_failures(identifier: str, ip: str) -> None:
    cache.delete(_lock_key(identifier, ip))


class OtpResult(enum.Enum):
    OK = "ok"
    WRONG = "wrong"
    EXPIRED = "expired"
    LOCKED = "locked"
    MISSING = "missing"


def _otp_hash(profile: UserProfile, code: str) -> str:
    return salted_hmac("accounts.otp", f"{profile.pk}:{code}").hexdigest()


def otp_resend_wait(session) -> int:
    sent_at = session.get("otp_sent_at")
    if not sent_at:
        return 0
    return max(0, int(OTP_RESEND_SECONDS - (time.time() - sent_at)))


def otp_attempts_left(session) -> int:
    return max(0, OTP_MAX_ATTEMPTS - session.get("otp_attempts", 0))


def issue_otp(session, profile: UserProfile) -> bool:
    """Send a fresh code. Returns False when throttled or when sending failed."""
    if otp_resend_wait(session) > 0:
        return False
    code = f"{secrets.randbelow(10**6):06d}"
    sent = send_sms(
        profile.phone_number, f"Your RideMate code is {code}. It expires in 10 minutes."
    )
    if not sent:
        return False
    session["otp_hash"] = _otp_hash(profile, code)
    session["otp_expires"] = time.time() + OTP_TTL_SECONDS
    session["otp_attempts"] = 0
    session["otp_sent_at"] = time.time()
    return True


def _clear_otp(session) -> None:
    for key in ("otp_hash", "otp_expires", "otp_attempts", "otp_sent_at"):
        session.pop(key, None)


def check_otp(session, profile: UserProfile, code: str) -> OtpResult:
    stored = session.get("otp_hash")
    if not stored:
        return OtpResult.MISSING
    if time.time() > session.get("otp_expires", 0):
        _clear_otp(session)
        return OtpResult.EXPIRED
    attempts = session.get("otp_attempts", 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        return OtpResult.LOCKED
    if constant_time_compare(stored, _otp_hash(profile, code.strip())):
        profile.is_verified = True
        profile.save(update_fields=["is_verified"])
        _clear_otp(session)
        return OtpResult.OK
    session["otp_attempts"] = attempts + 1
    return OtpResult.LOCKED if attempts + 1 >= OTP_MAX_ATTEMPTS else OtpResult.WRONG


def make_email_token(user) -> str:
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=EMAIL_SALT)


def confirm_email_token(token: str) -> UserProfile | None:
    try:
        data = signing.loads(token, salt=EMAIL_SALT, max_age=EMAIL_TOKEN_SECONDS)
    except signing.BadSignature:  # also covers SignatureExpired
        return None
    profile = (
        UserProfile.objects.select_related("user")
        .filter(user_id=data.get("uid"), user__email=data.get("email"))
        .first()
    )
    if profile is None:
        return None
    if not profile.email_verified:
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
    return profile


def send_confirmation_email(request, user) -> bool:
    url = request.build_absolute_uri(reverse("accounts:verify_email", args=[make_email_token(user)]))
    body = render_to_string("email/verify_email.txt", {"name": user.get_full_name(), "url": url})
    try:
        send_mail("Confirm your RideMate email", body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except (SMTPException, OSError):
        logger.exception("Confirmation email could not be sent.")
        return False
    return True





def get_viewer(request) -> UserProfile | None:
    """The signed-in member's profile, or None for a visitor."""
    return get_profile(request.user) if request.user.is_authenticated else None
