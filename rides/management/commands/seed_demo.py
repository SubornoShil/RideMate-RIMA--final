from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import UserProfile
from rides.models import RidePost
from trust.models import Circle, GuardianContact

DEMO_PASSWORD = "demo12345"
MEMBERS = [
    ("suborno", "Suborno Shil", "M", "01711000001", ["MIRPUR24", "DHAKAUNI"]),
    ("tanvir", "Tanvir Ahmed", "M", "01711000002", ["MIRPUR24"]),
    ("sadia", "Sadia Rahman", "F", "01711000003", ["DHAKAUNI"]),
    ("famin", "Famin Khan", "M", "01711000004", ["MIRPUR24", "DHAKAUNI"]),
    ("rafa", "Rafa Amon", "M", "01711000005", []),
]
# Earlier versions of this command created these accounts; --replace-old removes them.
OLD_DEMO_USERNAMES = ["nusrat", "rafi", "mehedi"]
CIRCLES = [
    ("MIRPUR24", "Mirpur Neighbours", "People who live and commute around Mirpur."),
    ("DHAKAUNI", "Dhaka Campus Commuters", "Students and staff travelling to campuses."),
]


class Command(BaseCommand):
    help = "Create demo members, circles and rides for local development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-production", action="store_true",
            help="Run even when DEBUG is off. Never use this on a live server.",
        )
        parser.add_argument(
            "--replace-old", action="store_true",
            help="Delete the earlier demo accounts (nusrat, rafi, mehedi) and their rides first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError("Refusing to create demo accounts while DEBUG is off.")

        if options["replace_old"]:
            removed, _ = User.objects.filter(username__in=OLD_DEMO_USERNAMES).delete()
            self.stdout.write(f"Removed {removed} old demo records.")

        circles = {
            code: Circle.objects.get_or_create(
                code=code, defaults={"name": name, "description": description}
            )[0]
            for code, name, description in CIRCLES
        }
        profiles = {}
        for username, full_name, gender, phone, circle_codes in MEMBERS:
            first, _, last = full_name.partition(" ")
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com", "first_name": first,
                          "last_name": last},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={"phone_number": phone, "gender": gender,
                          "is_verified": True, "email_verified": True},
            )
            for code in circle_codes:
                circles[code].members.add(profile)
            profiles[username] = profile

        for username, name, phone in [
            ("tanvir", "Tanvir's sister", "01811000010"),
            ("sadia", "Sadia's mother", "01911000011"),
            ("suborno", "Suborno's brother", "01611000012"),
        ]:
            GuardianContact.objects.get_or_create(
                user=profiles[username], guardian_phone=phone, defaults={"guardian_name": name}
            )

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        rides = [
            ("suborno", "Mirpur 10", "Motijheel", 1, 8, "CNG", 3, 60, False,
             "Leaving from the Mirpur 10 metro exit."),
            ("sadia", "Mirpur 1", "Dhanmondi 27", 1, 9, "CNG", 2, 70, True,
             "Women-only. Meet at the Mirpur 1 bus stop."),
            ("tanvir", "Mirpur 12", "Gulshan 2", 1, 9, "CAR", 3, 90, False, "Quiet ride, AC on."),
            ("famin", "Dhanmondi", "Uttara Sector 10", 2, 7, "BIKE", 1, 120, False, ""),
            ("sadia", "Banani", "Dhanmondi", 2, 17, "CNG", 2, 50, False, "Back from the office."),
            ("tanvir", "Dhaka Gabtoli", "Chattogram GEC Circle", 3, 6, "CAR", 3, 650, False,
             "Highway trip, one stop at Feni."),
            ("famin", "Sylhet Zindabazar", "Dhaka Gabtoli", 4, 7, "CAR", 2, 700, False, ""),
            ("suborno", "Rajshahi", "Bogura", 2, 15, "CAR", 3, 250, False, "One stop at Natore."),
            ("sadia", "Rajshahi", "Bogura", 3, 15, "CAR", 3, 250, True, "Women-only."),
        ]
        for username, start, end, days, hour, vehicle, seats, fare, women_only, note in rides:
            departure = (now + timedelta(days=days)).replace(hour=hour)
            RidePost.objects.get_or_create(
                creator=profiles[username], start_location=start, end_location=end,
                departure_time=departure,
                defaults={"vehicle_type": vehicle, "available_seats": seats,
                          "fare_per_seat": fare, "female_only": women_only, "note": note},
            )
        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready. Log in as suborno, tanvir, sadia, famin or rafa / {DEMO_PASSWORD}."
        ))
