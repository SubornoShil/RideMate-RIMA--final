from django.contrib.auth import authenticate
from django.core import mail
from django.core.exceptions import ValidationError
from django.urls import reverse

from accounts.forms import SignUpForm
from accounts.models import UserProfile
from trust.models import Circle
from accounts.phone import normalize_bd_phone

from accounts import services as accounts_services

from .factories import PASSWORD, BaseTestCase, make_member


def signup_data(**overrides):
    data = {
        "full_name": "Karim Uddin", "email": "karim@example.com", "username": "karim",
        "phone": "01712345678", "gender": "M", "password1": PASSWORD, "password2": PASSWORD,
        "circle_code": "", "accept_terms": "on",
    }
    data.update(overrides)
    return data


class PhoneTests(BaseTestCase):
    def test_accepted_formats_are_normalised(self):
        for raw in ["01712345678", "+8801712345678", "8801712345678", "017 1234-5678"]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_bd_phone(raw), "01712345678")

    def test_rejected_formats(self):
        for raw in ["01212345678", "0171234567", "017123456789", "abc", "", "+8801212345678"]:
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                normalize_bd_phone(raw)


class SignUpFormTests(BaseTestCase):
    def test_valid_form(self):
        form = SignUpForm(signup_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_email_is_case_insensitive(self):
        make_member("karim2")
        form = SignUpForm(signup_data(email="KARIM2@example.com"))
        self.assertIn("email", form.errors)

    def test_duplicate_username_and_phone(self):
        existing = make_member("karim")
        form = SignUpForm(signup_data(phone=existing.phone_number))
        self.assertIn("username", form.errors)
        self.assertIn("phone", form.errors)

    def test_password_rules(self):
        cases = {"12345678": "numeric", "short1A": "short", "password123": "common"}
        for password, label in cases.items():
            with self.subTest(label=label):
                form = SignUpForm(signup_data(password1=password, password2=password))
                self.assertIn("password1", form.errors)

    def test_password_mismatch_and_terms(self):
        form = SignUpForm(signup_data(password2="Different-Pass-99", accept_terms=""))
        self.assertIn("password2", form.errors)
        self.assertIn("accept_terms", form.errors)

    def test_unknown_circle_code(self):
        self.assertIn("circle_code", SignUpForm(signup_data(circle_code="NOPE")).errors)

    def test_post_creates_member_logs_in_and_sends_otp_and_email(self):
        Circle.objects.create(name="Mirpur", code="MIRPUR24")
        response = self.client.post(reverse("accounts:signup"), signup_data(circle_code="mirpur24"))
        self.assertRedirects(response, reverse("accounts:verify_phone"), fetch_redirect_response=False)
        profile = UserProfile.objects.get(user__username="karim")
        self.assertEqual(profile.phone_number, "01712345678")
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.circles.count(), 1)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertIn("otp_hash", self.client.session)
        self.assertEqual(len(mail.outbox), 1)


class LoginTests(BaseTestCase):
    def test_backend_accepts_email_or_username_any_case(self):
        make_member("alice")
        for identifier in ["alice", "ALICE", "Alice@Example.com"]:
            with self.subTest(identifier=identifier):
                self.assertIsNotNone(authenticate(username=identifier, password=PASSWORD))

    def test_wrong_password_and_unknown_account_both_fail(self):
        make_member("alice")
        self.assertIsNone(authenticate(username="alice", password="nope"))
        self.assertIsNone(authenticate(username="ghost", password="nope"))

    def test_lockout_after_five_failures_per_identifier_and_ip(self):
        for _ in range(5):
            accounts_services.register_login_failure("Alice", "1.2.3.4")
        self.assertTrue(accounts_services.is_login_locked("alice", "1.2.3.4"))
        self.assertFalse(accounts_services.is_login_locked("alice", "5.6.7.8"))
        accounts_services.clear_login_failures("alice", "1.2.3.4")
        self.assertFalse(accounts_services.is_login_locked("alice", "1.2.3.4"))

    def test_login_flow_blocks_correct_password_while_locked(self):
        make_member("alice")
        self.client.post(reverse("accounts:login"), {"step": "identifier", "identifier": "alice"})
        for _ in range(5):
            self.client.post(reverse("accounts:login"), {"step": "password", "password": "bad"})
        response = self.client.post(
            reverse("accounts:login"), {"step": "password", "password": PASSWORD}
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)

    def test_successful_two_step_login(self):
        make_member("alice")
        self.client.post(reverse("accounts:login"), {"step": "identifier", "identifier": "alice"})
        response = self.client.post(
            reverse("accounts:login"), {"step": "password", "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("rides:dashboard"), fetch_redirect_response=False)

    def test_logout_requires_post(self):
        make_member("alice")
        self.client.login(username="alice", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
