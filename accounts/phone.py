import re

from django.core.exceptions import ValidationError

_LOCAL = re.compile(r"^01[3-9]\d{8}$")


def normalize_bd_phone(raw: str) -> str:
    """Return a Bangladeshi mobile number as 01XXXXXXXXX or raise ValidationError."""
    value = re.sub(r"[\s\-()]", "", raw or "")
    if value.startswith("+880"):
        value = "0" + value[4:]
    elif value.startswith("880"):
        value = "0" + value[3:]
    if not _LOCAL.match(value):
        raise ValidationError(
            "Enter a Bangladeshi mobile number like 01712345678.", code="invalid_phone"
        )
    return value


def to_e164(local: str) -> str:
    return "+880" + local[1:]
