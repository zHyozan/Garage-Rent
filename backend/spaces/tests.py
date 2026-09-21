from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Space

User = get_user_model()


class SpaceApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="strong-pass-123")
        self.other_user = User.objects.create_user(username="other", password="strong-pass-123")
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

    def test_inactive_space_is_hidden_from_public(self):
        self.space.is_active = False
        self.space.save(update_fields=["is_active"])

        response = self.client.get(f"/api/spaces/{self.space.id}/")

        self.assertEqual(response.status_code, 404)

    def test_owner_can_edit_and_clear_optional_fields_with_multipart(self):
        self.space.length_m = 5
        self.space.save(update_fields=["length_m"])
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/spaces/{self.space.id}/", {
            "title": "Título atualizado", "length_m": "", "postal_code": "",
            "address_line": "Rua Nova, 20", "covered": "false",
        }, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.space.refresh_from_db()
        self.assertEqual(self.space.title, "Título atualizado")
        self.assertIsNone(self.space.length_m)
        self.assertEqual(self.space.postal_code, "")
        self.assertEqual(response.data["exact_address"]["address_line"], "Rua Nova, 20")
        self.assertFalse(self.space.covered)

    def test_other_user_cannot_edit_space(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.patch(f"/api/spaces/{self.space.id}/", {"title": "Alterado"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.space.refresh_from_db()
        self.assertEqual(self.space.title, "Garagem coberta")

    def test_other_user_cannot_retrieve_inactive_space(self):
        self.space.is_active = False
        self.space.save(update_fields=["is_active"])
        self.client.force_authenticate(self.other_user)

        response = self.client.get(f"/api/spaces/{self.space.id}/")

        self.assertEqual(response.status_code, 404)

    def test_owner_can_retrieve_and_reactivate_inactive_space(self):
        self.space.is_active = False
        self.space.save(update_fields=["is_active"])
        self.client.force_authenticate(self.owner)

        detail_response = self.client.get(f"/api/spaces/{self.space.id}/")
        reactivate_response = self.client.patch(
            f"/api/spaces/{self.space.id}/",
            {"is_active": True},
            format="json",
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(reactivate_response.status_code, 200)
        self.assertTrue(reactivate_response.data["is_active"])
        self.space.refresh_from_db()
        self.assertTrue(self.space.is_active)
