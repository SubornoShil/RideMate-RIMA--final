import re
from unittest import mock

from accounts.services import OtpResult

from accounts import services as accounts_services

from .factories import BaseTestCase, make_member


class OtpTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.profile = make_member("alice", verified=False)
        self.session = {}

    def issue(self):
        with mock.patch("accounts.services.send_sms", return_value=True) as sender:
            sent = accounts_services.issue_otp(self.session, self.profile)
        code = re.search(r"\b(\d{6})\b", sender.call_args.args[1]).group(1) if sent else None
        return sent, code, sender

    def test_correct_code_verifies(self):
        _, code, _ = self.issue()
        self.assertIs(accounts_services.check_otp(self.session, self.profile, code), OtpResult.OK)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_verified)
        self.assertNotIn("otp_hash", self.session)

    def test_session_stores_only_a_hash(self):
        _, code, _ = self.issue()
        self.assertNotIn(code, str(self.session))

    def test_wrong_code_counts_down_then_locks(self):
        _, code, _ = self.issue()
        wrong = "000000" if code != "000000" else "111111"
        results = [accounts_services.check_otp(self.session, self.profile, wrong) for _ in range(5)]
        self.assertEqual(results[:4], [OtpResult.WRONG] * 4)
        self.assertIs(results[4], OtpResult.LOCKED)
        self.assertIs(accounts_services.check_otp(self.session, self.profile, code), OtpResult.LOCKED)

    def test_expired_code(self):
        _, code, _ = self.issue()
        with mock.patch("accounts.services.time.time", return_value=self.session["otp_expires"] + 1):
            self.assertIs(accounts_services.check_otp(self.session, self.profile, code), OtpResult.EXPIRED)

    def test_missing_code(self):
        self.assertIs(accounts_services.check_otp({}, self.profile, "123456"), OtpResult.MISSING)

    def test_resend_wait(self):
        sent, _, _ = self.issue()
        self.assertTrue(sent)
        self.assertGreater(accounts_services.otp_resend_wait(self.session), 0)
        with mock.patch("accounts.services.send_sms") as sender:
            self.assertFalse(accounts_services.issue_otp(self.session, self.profile))
        sender.assert_not_called()
        with mock.patch(
            "accounts.services.time.time", return_value=self.session["otp_sent_at"] + 61
        ):
            self.assertEqual(accounts_services.otp_resend_wait(self.session), 0)

    def test_failed_sms_returns_false(self):
        with mock.patch("accounts.services.send_sms", return_value=False):
            self.assertFalse(accounts_services.issue_otp(self.session, self.profile))
        self.assertNotIn("otp_hash", self.session)
