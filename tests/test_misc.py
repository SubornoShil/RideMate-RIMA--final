from django.test import override_settings
from django.urls import reverse

from accounts.sms import send_sms

from .factories import PASSWORD, BaseTestCase, make_member


class MiscTests(BaseTestCase):
    def test_designed_404(self):
        response = self.client.get("/definitely-not-here/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)

    def test_healthz(self):
        self.assertEqual(self.client.get(reverse("healthz")).json(), {"status": "ok"})

    def test_security_headers_are_set(self):
        response = self.client.get(reverse("healthz"))
        self.assertIn("Permissions-Policy", response)

    def test_analytics_is_staff_only(self):
        make_member("alice")
        self.client.login(username="alice", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("trust:analytics")).status_code, 403)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("rides:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_unverified_member_cannot_open_ride_form(self):
        make_member("alice", verified=False)
        self.client.login(username="alice", password=PASSWORD)
        response = self.client.get(reverse("rides:ride_new"))
        self.assertRedirects(response, reverse("accounts:verify_phone"), fetch_redirect_response=False)

    @override_settings(SMS_BACKEND="nonsense")
    def test_send_sms_never_raises(self):
        self.assertFalse(send_sms("01712345678", "hi"))

    @override_settings(SMS_BACKEND="console")
    def test_console_backend_returns_true(self):
        self.assertTrue(send_sms("01712345678", "hi"))
