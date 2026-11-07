from unittest import mock

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from trust.forms import GuardianForm
from trust.models import GuardianContact, Review
from config.errors import RideError

from rides import services as rides_services
from trust import services as trust_services

from .factories import PASSWORD, BaseTestCase, make_member, make_ride


class ReviewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.host = make_member("host")
        self.rider = make_member("rider")
        self.newbie = make_member("newbie", days_old=2)
        self.ride = make_ride(self.host, available_seats=3)
        for member in (self.rider, self.newbie):
            request = rides_services.send_request(self.ride, member)
            rides_services.decide_request(request.pk, self.host, accept=True)

    def complete(self):
        rides_services.complete_ride(self.ride.pk, self.host)
        self.ride.refresh_from_db()

    def test_cannot_review_before_completion(self):
        with self.assertRaises(RideError):
            trust_services.submit_review(self.ride, self.rider, self.host, 5)

    def test_weights_and_trust_maths(self):
        self.complete()
        trust_services.submit_review(self.ride, self.rider, self.host, 5)
        trust_services.submit_review(self.ride, self.newbie, self.host, 3)
        weights = dict(Review.objects.values_list("rater__user__username", "rater_weight"))
        self.assertEqual(weights, {"rider": 1.0, "newbie": 0.5})
        self.host.refresh_from_db()
        self.assertEqual(self.host.trust_score, 86.7)  # (5*1 + 3*0.5) / 1.5 * 20
        self.assertEqual(self.host.trust_label, "Good")

    def test_pending_reviews_lists_partners_until_rated(self):
        self.assertEqual(trust_services.pending_reviews(self.rider), [])  # ride not finished yet
        self.complete()
        pending = trust_services.pending_reviews(self.rider)
        self.assertEqual(len(pending), 1)
        names = {p.pk for p in pending[0]["people"]}
        self.assertEqual(names, {self.host.pk, self.newbie.pk})
        trust_services.submit_review(self.ride, self.rider, self.host, 5)
        trust_services.submit_review(self.ride, self.rider, self.newbie, 4)
        self.assertEqual(trust_services.pending_reviews(self.rider), [])

    def test_ride_page_shows_rating_panel(self):
        self.client.login(username="rider", password=PASSWORD)
        response = self.client.get(self.ride.get_absolute_url())
        self.assertContains(response, "Rate your ride partner")
        self.assertContains(response, "Opens after the ride")

    def test_labels(self):
        cases = {100: "Excellent", 90: "Excellent", 89.9: "Good", 75: "Good",
                 74.9: "Fair", 60: "Fair", 59.9: "Low"}
        for score, label in cases.items():
            with self.subTest(score=score):
                self.host.trust_score = score
                self.assertEqual(self.host.trust_label, label)

    def test_review_rules(self):
        outsider = make_member("outsider")
        self.complete()
        with self.assertRaises(RideError):
            trust_services.submit_review(self.ride, self.host, self.host, 5)
        with self.assertRaises(RideError):
            trust_services.submit_review(self.ride, outsider, self.host, 5)
        with self.assertRaises(RideError):
            trust_services.submit_review(self.ride, self.rider, outsider, 5)
        trust_services.submit_review(self.ride, self.rider, self.host, 4, "Smooth.")
        with self.assertRaises(RideError):
            trust_services.submit_review(self.ride, self.rider, self.host, 5)

    def test_database_blocks_bad_scores(self):
        self.complete()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(ride=self.ride, rater=self.rider, rated_user=self.host, score=6)

    def test_reviewed_member_is_notified(self):
        self.complete()
        trust_services.submit_review(self.ride, self.rider, self.host, 5)
        self.assertTrue(self.host.notifications.filter(message__contains="5-star").exists())


class GuardianTests(BaseTestCase):
    def test_limit_of_three(self):
        member = make_member("alice")
        for index in range(3):
            trust_services.add_guardian(member, f"G{index}", f"0181100000{index}")
        with self.assertRaises(RideError):
            trust_services.add_guardian(member, "Fourth", "01811000009")
        self.assertEqual(GuardianContact.objects.filter(user=member).count(), 3)

    def test_phone_is_validated_and_normalised(self):
        form = GuardianForm({"guardian_name": "Ma", "guardian_phone": "+8801811000001"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["guardian_phone"], "01811000001")
        self.assertFalse(GuardianForm({"guardian_name": "Ma", "guardian_phone": "123"}).is_valid())
        self.assertTrue(ValidationError)

    def test_accepting_a_request_alerts_both_sides_guardians(self):
        host, rider = make_member("host"), make_member("rider")
        trust_services.add_guardian(host, "Host Mum", "01811000001")
        trust_services.add_guardian(rider, "Rider Dad", "01811000002")
        trust_services.add_guardian(rider, "Rider Aunt", "01811000003")
        ride = make_ride(host)
        request = rides_services.send_request(ride, rider)
        with mock.patch("trust.services.send_sms", return_value=True) as sender:
            with self.captureOnCommitCallbacks(execute=True):
                rides_services.decide_request(request.pk, host, accept=True)
        self.assertEqual(sender.call_count, 3)
        self.assertIn("Mirpur 10", sender.call_args.args[1])
        self.assertTrue(rider.notifications.filter(kind="GUARDIAN").exists())
        self.assertTrue(host.notifications.filter(kind="GUARDIAN").exists())
