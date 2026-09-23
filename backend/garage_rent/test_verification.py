from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase
from spaces.models import EmailVerification
from .email_verification import SALT


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailVerificationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(username='verify', email='verify@example.com')
        self.client.force_authenticate(self.user)

    def test_request_and_confirm(self):
        self.assertFalse(self.client.get('/api/auth/users/me/').data['email_verified'])
        result = self.client.post('/api/auth/verify-email/')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        token = mail.outbox[0].body.split('token=')[1].strip()
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post('/api/auth/verify-email/confirm/', {'token': token}).status_code, 200)
        self.user.refresh_from_db()
        self.client.force_authenticate(self.user)
        self.assertTrue(self.client.get('/api/auth/users/me/').data['email_verified'])

    def test_invalid_expired_and_changed_email(self):
        token = signing.dumps({'user': self.user.pk, 'email': self.user.email}, salt=SALT)
        self.assertEqual(self.client.post('/api/auth/verify-email/confirm/', {'token': token + 'x'}).status_code, 400)
        with patch('django.core.signing.time.time', return_value=1):
            expired = signing.dumps({'user': self.user.pk, 'email': self.user.email}, salt=SALT)
        self.assertEqual(self.client.post('/api/auth/verify-email/confirm/', {'token': expired}).status_code, 400)
        self.user.email = 'changed@example.com'
        self.user.save()
        self.assertEqual(self.client.post('/api/auth/verify-email/confirm/', {'token': token}).status_code, 400)
        self.assertFalse(EmailVerification.objects.exists())

    def test_unauthenticated_request_and_mail_failure(self):
        with patch('garage_rent.email_verification.send_mail', side_effect=OSError):
            self.assertEqual(self.client.post('/api/auth/verify-email/').status_code, 503)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post('/api/auth/verify-email/').status_code, 401)
