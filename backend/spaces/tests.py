from io import BytesIO
from datetime import timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from reservations.models import Reservation
from .models import Space

User = get_user_model()


class SpaceApiTests(APITestCase):
    def image_file(self, name):
        buffer = BytesIO()
        Image.new("RGB", (2, 2), "blue").save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

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

    def test_owner_can_create_pause_view_and_reactivate_space(self):
        self.client.force_authenticate(self.owner)
        create_response = self.client.post("/api/spaces/", {
            "title": "Nova garagem",
            "description": "Garagem para locação",
            "price": "250.00",
            "billing_period": Space.BillingPeriod.MONTH,
            "state": "SP",
            "city": "São Paulo",
            "neighborhood": "Tatuapé",
            "address_line": "Rua Nova, 20",
        }, format="json")
        self.assertEqual(create_response.status_code, 201)
        space_id = create_response.data["id"]
        detail_url = f"/api/spaces/{space_id}/"

        pause_response = self.client.patch(detail_url, {"is_active": False}, format="json")
        self.assertEqual(pause_response.status_code, 200)
        self.assertFalse(pause_response.data["is_active"])

        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        self.assertTrue(detail_response.data["is_owner"])
        mine_response = self.client.get("/api/spaces/mine/")
        self.assertIn(space_id, [space["id"] for space in mine_response.data["results"]])

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get(detail_url).status_code, 404)

        self.client.force_authenticate(self.owner)
        reactivate_response = self.client.patch(
            detail_url,
            {"is_active": True},
            format="json",
        )

        self.assertEqual(reactivate_response.status_code, 200)
        self.assertTrue(reactivate_response.data["is_active"])
        self.assertTrue(Space.objects.get(pk=space_id).is_active)

    def test_image_limit_and_gallery_response(self):
        self.client.force_authenticate(self.owner)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post("/api/spaces/", {
                "title": "Garagem com galeria",
                "description": "Oito fotos da garagem",
                "price": "250.00",
                "billing_period": Space.BillingPeriod.MONTH,
                "state": "SP",
                "city": "São Paulo",
                "neighborhood": "Tatuapé",
                "address_line": "Rua Nova, 20",
                "images_upload": [self.image_file(f"photo-{index}.png") for index in range(8)],
            }, format="multipart")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(len(response.data["images"]), 8)
            self.assertEqual(response.data["cover_image"], response.data["images"][0]["url"])

            rejected = self.client.patch(f"/api/spaces/{response.data['id']}/", {
                "images_upload": [self.image_file("extra.png")],
            }, format="multipart")
            self.assertEqual(rejected.status_code, 400)
            self.assertEqual(Space.objects.get(pk=response.data["id"]).images.count(), 8)

    def test_owner_can_reorder_and_remove_images(self):
        self.client.force_authenticate(self.owner)
        url = f"/api/spaces/{self.space.id}/"
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            uploaded = self.client.patch(url, {
                "images_upload": [self.image_file(f"photo-{index}.png") for index in range(3)],
            }, format="multipart")
            self.assertEqual(uploaded.status_code, 200)
            ids = [image["id"] for image in uploaded.data["images"]]
            updated = self.client.patch(url, {
                "remove_image_ids": [ids[1]],
                "gallery_order": [f"old:{ids[2]}", f"old:{ids[0]}"],
            }, format="multipart")
            self.assertEqual(updated.status_code, 200)
            self.assertEqual([image["id"] for image in updated.data["images"]], [ids[2], ids[0]])
            self.assertEqual(updated.data["cover_image"], updated.data["images"][0]["url"])
            replaced_cover = self.client.patch(url, {
                "images_upload": [self.image_file("new-cover.png")],
                "gallery_order": ["new:0", f"old:{ids[2]}", f"old:{ids[0]}"],
            }, format="multipart")
            self.assertEqual(replaced_cover.status_code, 200)
            self.assertEqual(replaced_cover.data["images"][0]["id"], self.space.images.first().id)
            self.assertEqual(replaced_cover.data["cover_image"], replaced_cover.data["images"][0]["url"])

    def test_image_size_limit_is_enforced(self):
        self.client.force_authenticate(self.owner)
        image = self.image_file("large.png")
        large = SimpleUploadedFile("large.png", image.read() + b"0" * (5 * 1024 * 1024), content_type="image/png")
        response = self.client.patch(f"/api/spaces/{self.space.id}/", {
            "images_upload": [large],
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.space.images.count(), 0)

    def test_availability_exposes_only_active_reservation_periods(self):
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=3)
        reservation = Reservation.objects.create(
            space=self.space, renter=self.other_user, start_at=start, end_at=end,
            status=Reservation.Status.PENDING, unit_price=self.space.price, total_amount=self.space.price,
        )
        url = f"/api/spaces/{self.space.id}/availability/"
        params = {"from": start.date().isoformat(), "to": (end.date() + timedelta(days=1)).isoformat()}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(set(response.data[0]), {"start_at", "end_at"})
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
        self.assertEqual(self.client.get(url, params).data, [])
