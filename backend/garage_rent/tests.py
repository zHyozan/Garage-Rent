from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase


class EmailAuthenticationTests(APITestCase):
    def test_existing_user_logs_in_with_email(self):
        get_user_model().objects.create_user(
            username="owner", email="Owner@Example.com", password="SenhaForte1!"
        )

        response = self.client.post("/api/auth/jwt/create/", {
            "email": "owner@example.com", "password": "SenhaForte1!",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertEqual(self.client.post("/api/auth/jwt/create/", {
            "username": "owner", "password": "SenhaForte1!",
        }, format="json").status_code, 400)

    def test_registration_requires_uppercase_number_and_symbol(self):
        base = {
            "username": "newuser", "email": "new@example.com",
        }
        for password in ("senhaforte1!", "SenhaForte!!", "SenhaForte11"):
            response = self.client.post("/api/auth/users/", {
                **base, "password": password, "re_password": password,
            }, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("password", response.data)

        response = self.client.post("/api/auth/users/", {
            **base, "password": "SenhaForte1!", "re_password": "SenhaForte1!",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(get_user_model().objects.filter(email="new@example.com").count(), 1)
        login = self.client.post("/api/auth/jwt/create/", {
            "email": "new@example.com", "password": "SenhaForte1!",
        }, format="json")
        self.assertEqual(login.status_code, 200)

    def test_registration_rejects_duplicate_email_ignoring_case(self):
        get_user_model().objects.create_user(
            username="owner", email="Owner@Example.com", password="SenhaForte1!"
        )
        response = self.client.post("/api/auth/users/", {
            "username": "another", "email": "owner@example.com",
            "password": "OutraSenha1!", "re_password": "OutraSenha1!",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_uses_email_link_and_invalidates_old_password(self):
        user = get_user_model().objects.create_user(
            username="owner", email="owner@example.com", password="SenhaAntiga1!"
        )
        request = self.client.post("/api/auth/password-reset/", {"email": user.email}, format="json")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        link = next(line for line in mail.outbox[0].body.splitlines() if line.startswith("http"))
        params = parse_qs(urlparse(link).query)
        reset = self.client.post("/api/auth/password-reset/confirm/", {
            "uid": params["uid"][0], "token": params["token"][0],
            "password": "SenhaNova2!", "re_password": "SenhaNova2!",
        }, format="json")
        self.assertEqual(reset.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("SenhaNova2!"))
        self.assertFalse(user.check_password("SenhaAntiga1!"))
        self.assertEqual(self.client.post("/api/auth/password-reset/confirm/", {
            "uid": params["uid"][0], "token": params["token"][0],
            "password": "OutraSenha3!", "re_password": "OutraSenha3!",
        }, format="json").status_code, 400)
        unknown = self.client.post("/api/auth/password-reset/", {"email": "missing@example.com"}, format="json")
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
