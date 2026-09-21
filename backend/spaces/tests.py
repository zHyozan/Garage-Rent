from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Space

User = get_user_model()


class SpaceApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="strong-pass-123")
        self.space = Space.objects.create(
            owner=self.owner,
            title="Garagem coberta",
            description="Garagem residencial",
            price=500,
            billing_period=Space.BillingPeriod.MONTH,
            state="SP",
            city="São Paulo",
            neighborhood="Tatuapé",
            postal_code="00000-000",
            address_line="Rua Exemplo, 100",
        )

    def test_public_detail_hides_exact_address(self):
        response = self.client.get(f"/api/spaces/{self.space.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["exact_address"])
        self.assertNotIn("address_line", response.data)
