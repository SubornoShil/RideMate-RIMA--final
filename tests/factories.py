import itertools
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import UserProfile
from rides.models import RidePost

PASSWORD = "Tr1cky-Horse-42"
_numbers = itertools.count(1)


def make_member(username, gender="M", verified=True, days_old=30):
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD,
        first_name=username.title(),
    )
    profile = UserProfile.objects.create(
        user=user, phone_number=f"017{next(_numbers):08d}", gender=gender,
        is_verified=verified, email_verified=True,
    )
    UserProfile.objects.filter(pk=profile.pk).update(
        created_at=timezone.now() - timedelta(days=days_old)
    )
    profile.refresh_from_db()
    return profile


def make_ride(host, **overrides):
    values = {
        "creator": host, "start_location": "Mirpur 10", "end_location": "Motijheel",
        "departure_time": timezone.now() + timedelta(days=1), "vehicle_type": "CNG",
        "available_seats": 2, "fare_per_seat": 50,
    }
    values.update(overrides)
    return RidePost.objects.create(**values)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BaseTestCase(TestCase):
    def setUp(self):
        cache.clear()
