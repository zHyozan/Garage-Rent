from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from spaces.models import Space
from .models import Reservation

User = get_user_model()


class ReservationApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner2", password="strong-pass-123")
        self.renter = User.objects.create_user(username="renter", password="strong-pass-123")
        self.space = Space.objects.create(
            owner=self.owner,
            title="Galpão",
            description="Galpão para armazenagem",
            price=100,
            billing_period=Space.BillingPeriod.DAY,
            state="SP",
            city="São Paulo",
            neighborhood="Mooca",
            address_line="Rua Privada, 10",
        )
        self.client.force_authenticate(self.renter)

    def test_blocks_overlapping_reservation(self):
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(days=2)
        Reservation.objects.create(
            space=self.space,
            renter=self.renter,
            start_at=start,
            end_at=end,
            unit_price=100,
            total_amount=200,
            status=Reservation.Status.CONFIRMED,
        )
        response = self.client.post("/api/reservations/", {
            "space": self.space.id,
            "start_at": (start + timedelta(hours=12)).isoformat(),
            "end_at": (end + timedelta(days=1)).isoformat(),
        }, format="json")
        self.assertEqual(response.status_code, 400)
