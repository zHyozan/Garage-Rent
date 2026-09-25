from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from spaces.models import Space
from .models import Reservation


class ReservationArchiveTests(APITestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="owner")
        self.renter = users.objects.create_user(username="renter")
        self.other = users.objects.create_user(username="other")
        self.space = Space.objects.create(owner=self.owner, title="Vaga", description="Coberta", price=Decimal('12.50'), billing_period="hour", city="São Paulo", state="SP", neighborhood="Centro", address_line="Endereço privado")
        self.record = Reservation.objects.create(space=self.space, renter=self.renter, start_at=timezone.now()-timedelta(days=2), end_at=timezone.now()-timedelta(days=1), status="confirmed", unit_price=12.50, total_amount=300)
        self.client.force_authenticate(self.renter)

    def test_history_is_visible_only_to_participants(self):
        for user in [self.owner, self.renter]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get('/api/reservations/').data['count'], 1)
            self.assertEqual(self.client.get(f'/api/reservations/{self.record.pk}/').status_code, 200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/reservations/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/reservations/{self.record.pk}/').status_code, 404)

    def test_archive_rejects_writes_and_old_booking_actions(self):
        self.assertEqual(self.client.post('/api/reservations/', {}).status_code, 405)
        self.assertEqual(self.client.patch(f'/api/reservations/{self.record.pk}/', {'status': 'cancelled'}).status_code, 405)
        for action in ['complete', 'cancel', 'confirm', 'reject', 'review']:
            self.assertEqual(self.client.post(f'/api/reservations/{self.record.pk}/{action}/').status_code, 404)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'confirmed')

    def test_historical_pricing_calculation_is_preserved(self):
        for period, duration, total in [('hour', timedelta(minutes=61), '25.00'), ('day', timedelta(hours=25), '25.00'), ('month', timedelta(days=31), '25.00')]:
            self.space.billing_period = period
            self.record.end_at = self.record.start_at + duration
            self.assertEqual(self.record.calculate_total(), Decimal(total))
