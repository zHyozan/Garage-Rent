from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from spaces.models import Space
from .models import Reservation, Review


class ReservationImprovementsTests(APITestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="owner", email="owner@example.com")
        self.renter = users.objects.create_user(username="renter", email="renter@example.com")
        self.other = users.objects.create_user(username="other")
        self.space = Space.objects.create(owner=self.owner, title="Vaga", description="Coberta", price=Decimal('12.50'), billing_period="hour", city="São Paulo", state="SP", neighborhood="Centro", address_line="Endereço privado")
        self.client.force_authenticate(self.renter)
        self.start = timezone.now() + timedelta(days=3)
        self.payload = {"space": self.space.id, "start_at": self.start.isoformat(), "end_at": (self.start + timedelta(minutes=61)).isoformat()}

    def reservation(self, **kwargs):
        values = dict(space=self.space, renter=self.renter, start_at=timezone.now() - timedelta(days=2), end_at=timezone.now() - timedelta(days=1), status="confirmed", unit_price=12.50, total_amount=25)
        values.update(kwargs)
        return Reservation.objects.create(**values)

    def test_quote_rounds_units_and_does_not_create_reservation(self):
        result = self.client.post('/api/reservations/quote/', self.payload, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['total_amount'], '25.00')
        self.assertIn('Cancelamento', result.data['cancellation_policy'])
        self.assertFalse(Reservation.objects.exists())

    def test_quote_overlap_and_stale_price_are_rejected(self):
        result = self.client.post('/api/reservations/', {**self.payload, 'expected_total': '20.00'}, format='json')
        self.assertEqual(result.status_code, 400)
        self.assertFalse(Reservation.objects.exists())
        result = self.client.post('/api/reservations/', {**self.payload, 'expected_total': '25.00'}, format='json')
        self.assertEqual(result.status_code, 201)
        self.assertEqual(self.client.post('/api/reservations/quote/', self.payload, format='json').status_code, 400)

    def test_day_and_month_pricing(self):
        for period, duration, total in [('day', timedelta(hours=25), '25.00'), ('month', timedelta(days=31), '25.00')]:
            self.space.billing_period = period
            self.space.save()
            result = self.client.post('/api/reservations/quote/', {**self.payload, 'end_at': (self.start + duration).isoformat()}, format='json')
            self.assertEqual(result.data['total_amount'], total)

    def test_quote_rejects_past_inactive_and_owner(self):
        self.assertEqual(self.client.post('/api/reservations/quote/', {**self.payload, 'start_at': (timezone.now() - timedelta(days=1)).isoformat()}, format='json').status_code, 400)
        self.space.is_active = False
        self.space.save()
        self.assertEqual(self.client.post('/api/reservations/quote/', self.payload, format='json').status_code, 400)
        self.space.is_active = True
        self.space.save()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post('/api/reservations/quote/', self.payload, format='json').status_code, 400)

    def test_complete_then_review_and_public_summary(self):
        item = self.reservation()
        self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/complete/').status_code, 200)
        result = self.client.post(f'/api/reservations/{item.pk}/review/', {'score': 4, 'comment': 'Bom acesso'}, format='json')
        self.assertEqual(result.status_code, 201)
        self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/review/', {'score': 5}, format='json').status_code, 400)
        self.client.force_authenticate(None)
        result = self.client.get(f'/api/spaces/{self.space.pk}/')
        self.assertEqual(result.data['rating'], {'average': 4.0, 'count': 1})
        self.assertIsNone(result.data['exact_address'])
        reviews = self.client.get(f'/api/spaces/{self.space.pk}/reviews/')
        self.assertEqual(reviews.data['results'][0]['comment'], 'Bom acesso')
        self.assertNotIn('email', reviews.data['results'][0])

    def test_unrelated_user_cannot_complete_or_review(self):
        item = self.reservation()
        self.client.force_authenticate(self.other)
        for action in ['complete', 'review', 'cancel']:
            self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/{action}/', {'score': 5}).status_code, 404)

    def test_future_and_pending_reservations_cannot_complete_or_review(self):
        for status, end in [('confirmed', self.start), ('pending', timezone.now() - timedelta(days=1))]:
            item = self.reservation(status=status, end_at=end)
            self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/complete/').status_code, 400)
            self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/review/', {'score': 5}).status_code, 400)

    def test_review_score_and_owner_restricted(self):
        item = self.reservation(status='completed')
        for score in [0, 6, 'invalid']:
            self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/review/', {'score': score}).status_code, 400)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(f'/api/reservations/{item.pk}/review/', {'score': 5}).status_code, 403)
        self.assertFalse(Review.objects.exists())

    def test_cancel_policy(self):
        ended = self.reservation()
        self.assertEqual(self.client.post(f'/api/reservations/{ended.pk}/cancel/').status_code, 400)
        future = self.reservation(start_at=self.start, end_at=self.start + timedelta(days=1))
        self.assertEqual(self.client.post(f'/api/reservations/{future.pk}/cancel/').status_code, 200)
