from django.contrib.auth import get_user_model
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
