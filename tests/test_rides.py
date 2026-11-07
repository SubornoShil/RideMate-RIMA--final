from datetime import timedelta
from unittest import mock

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from rides.models import RidePost, RideRequest
from trust.models import Notification
from config.errors import RideError

from rides import services as rides_services

from .factories import PASSWORD, BaseTestCase, make_member, make_ride


class VisibilityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.woman = make_member("nusrat", gender="F")
        self.man = make_member("tanvir", gender="M")
        self.open_ride = make_ride(self.man)
        self.women_ride = make_ride(self.woman, female_only=True)

    def test_search_hides_women_only_from_men_and_anonymous(self):
        for viewer in (self.man, None):
            with self.subTest(viewer=viewer):
                self.assertEqual(rides_services.search_rides(viewer), [self.open_ride])

    def test_women_see_everything_and_can_filter(self):
        self.assertEqual(len(rides_services.search_rides(self.woman)), 2)
        self.assertEqual(rides_services.search_rides(self.woman, women_only=True), [self.women_ride])

    def test_non_woman_cannot_force_the_filter(self):
        self.assertEqual(rides_services.search_rides(self.man, women_only=True), [self.open_ride])

    def test_direct_url_is_blocked_for_men_and_anonymous(self):
        url = reverse("rides:ride_detail", args=[self.women_ride.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.login(username="tanvir", password=PASSWORD)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_woman_can_open_women_only_ride(self):
        self.client.login(username="nusrat", password=PASSWORD)
        url = reverse("rides:ride_detail", args=[self.women_ride.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_only_future_open_rides_with_seats_are_listed(self):
        make_ride(self.man, departure_time=timezone.now() - timedelta(hours=1))
        make_ride(self.man, available_seats=0, status=RidePost.Status.FILLED)
        self.assertEqual(rides_services.search_rides(self.man), [self.open_ride])

    def test_circle_rides_come_first(self):
        from trust.models import Circle

        stranger = make_member("stranger")
        friend = make_member("friend")
        later = make_ride(friend, departure_time=timezone.now() + timedelta(days=3))
        make_ride(stranger, departure_time=timezone.now() + timedelta(hours=2))
        circle = Circle.objects.create(name="C", code="C1")
        circle.members.add(self.man, friend)
        ordered = rides_services.search_rides(self.man)
        self.assertEqual(ordered[0], later)
        self.assertTrue(ordered[0].in_circle)


class RequestFlowTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.host = make_member("host", gender="F")
        self.a = make_member("amina", gender="F")
        self.b = make_member("bina", gender="F")
        self.ride = make_ride(self.host, available_seats=1)

    def request_for(self, member):
        return rides_services.send_request(self.ride, member)

    def test_last_seat_cannot_be_oversold(self):
        first, second = self.request_for(self.a), self.request_for(self.b)
        rides_services.decide_request(first.pk, self.host, accept=True)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.available_seats, 0)
        self.assertEqual(self.ride.status, RidePost.Status.FILLED)
        with self.assertRaises(RideError):
            rides_services.decide_request(second.pk, self.host, accept=True)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.available_seats, 0)

    def test_accept_decreases_seats(self):
        self.ride.available_seats = 3
        self.ride.save()
        rides_services.decide_request(self.request_for(self.a).pk, self.host, accept=True)
        self.ride.refresh_from_db()
        self.assertEqual((self.ride.available_seats, self.ride.status), (2, RidePost.Status.OPEN))

    def test_cancelling_accepted_request_returns_seat_and_reopens(self):
        request = self.request_for(self.a)
        rides_services.decide_request(request.pk, self.host, accept=True)
        rides_services.cancel_request(request.pk, self.a)
        self.ride.refresh_from_db()
        self.assertEqual((self.ride.available_seats, self.ride.status), (1, RidePost.Status.OPEN))

    def test_only_host_can_decide_complete_or_cancel(self):
        request = self.request_for(self.a)
        with self.assertRaises(PermissionDenied):
            rides_services.decide_request(request.pk, self.b, accept=True)
        with self.assertRaises(PermissionDenied):
            rides_services.complete_ride(self.ride.pk, self.a)
        with self.assertRaises(PermissionDenied):
            rides_services.cancel_ride(self.ride.pk, self.a)

    def test_only_requester_can_cancel_request(self):
        request = self.request_for(self.a)
        with self.assertRaises(PermissionDenied):
            rides_services.cancel_request(request.pk, self.b)

    def test_request_rules(self):
        with self.assertRaises(RideError):
            rides_services.send_request(self.ride, self.host)
        male = make_member("man", gender="M")
        women_ride = make_ride(self.host, female_only=True)
        with self.assertRaises(RideError):
            rides_services.send_request(women_ride, male)
        unverified = make_member("new", gender="F", verified=False)
        with self.assertRaises(RideError):
            rides_services.send_request(self.ride, unverified)
        self.request_for(self.a)
        with self.assertRaises(RideError):
            self.request_for(self.a)

    def test_cancelled_request_can_be_resent(self):
        request = self.request_for(self.a)
        rides_services.cancel_request(request.pk, self.a)
        again = self.request_for(self.a)
        self.assertEqual((again.pk, again.status), (request.pk, RideRequest.Status.PENDING))

    def test_database_rejects_duplicate_requests(self):
        self.request_for(self.a)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RideRequest.objects.create(ride=self.ride, requester=self.a)

    def test_reject_leaves_seats_alone(self):
        request = self.request_for(self.a)
        rides_services.decide_request(request.pk, self.host, accept=False)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.available_seats, 1)

    def test_cancel_ride_cancels_requests_and_notifies(self):
        accepted, pending = self.request_for(self.a), self.request_for(self.b)
        rides_services.decide_request(accepted.pk, self.host, accept=True)
        self.ride.available_seats = 2
        self.ride.status = RidePost.Status.OPEN
        self.ride.save()
        rides_services.cancel_ride(self.ride.pk, self.host)
        statuses = set(RideRequest.objects.values_list("status", flat=True))
        self.assertEqual(statuses, {RideRequest.Status.CANCELLED})
        self.assertTrue(Notification.objects.filter(user=self.b, message__contains="cancelled").exists())

    def test_complete_notifies_accepted_riders(self):
        self.ride.available_seats = 2
        self.ride.save()
        rides_services.decide_request(self.request_for(self.a).pk, self.host, accept=True)
        rides_services.complete_ride(self.ride.pk, self.host)
        self.assertTrue(
            Notification.objects.filter(user=self.a, kind=Notification.Kind.REVIEW).exists()
        )

    def test_contacts_only_for_host_and_accepted_riders(self):
        self.ride.available_seats = 3
        self.ride.save()
        pending, accepted = self.request_for(self.a), self.request_for(self.b)
        rides_services.decide_request(accepted.pk, self.host, accept=True)
        outsider = make_member("outsider", gender="F")
        self.assertEqual(rides_services.ride_contacts(None, self.ride), [])
        self.assertEqual(rides_services.ride_contacts(outsider, self.ride), [])
        self.assertEqual(rides_services.ride_contacts(self.a, self.ride), [])
        host_view = rides_services.ride_contacts(self.host, self.ride)
        self.assertEqual([c["phone"] for c in host_view], [self.b.phone_number])
        rider_view = rides_services.ride_contacts(self.b, self.ride)
        self.assertEqual([c["phone"] for c in rider_view], [self.host.phone_number])
        self.assertIsNotNone(pending)

    def test_detail_page_never_prints_phone_to_outsiders(self):
        make_member("outsider", gender="F")
        self.client.login(username="outsider", password=PASSWORD)
        response = self.client.get(reverse("rides:ride_detail", args=[self.ride.pk]))
        self.assertNotContains(response, self.host.phone_number)

    def test_state_changes_reject_get(self):
        self.client.login(username="amina", password=PASSWORD)
        url = reverse("rides:ride_request", args=[self.ride.pk])
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_model_helpers(self):
        self.assertIn("google.com/maps/dir", self.ride.maps_url)
        self.assertTrue(self.ride.is_bookable)
        self.ride.departure_time = timezone.now() - timedelta(minutes=1)
        self.assertFalse(self.ride.is_bookable)
        self.assertTrue(mock)
