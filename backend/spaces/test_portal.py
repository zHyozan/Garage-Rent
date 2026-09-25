from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import RequestFactory, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .admin import PromotionAdmin
from .models import (Space, PromotionPackage, Promotion, ListingEvent, Inquiry,
                     ServiceReview, ListingReport, SavedAlert, EmailVerification, NotificationDelivery)
from reservations.models import Reservation, Review


class PortalTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        users = get_user_model()
        self.owner = users.objects.create_user(username='owner', email='owner@example.com')
        self.visitor = users.objects.create_user(username='visitor', email='visitor@example.com')
        self.other = users.objects.create_user(username='other', email='other@example.com')
        self.space = Space.objects.create(owner=self.owner, title='Vaga coberta', description='Vaga residencial', price=400,
            city='São Paulo', state='SP', neighborhood='Centro', address_line='Endereço privado', contact_phone='5511999999999')
        self.package = PromotionPackage.objects.first()
        self.client.force_authenticate(self.owner)

    def url(self, action):
        return f'/api/portal/{self.space.pk}/{action}/'

    def request_promotion(self):
        return self.client.post(self.url('promotions'), {'package': self.package.pk}, format='json')

    def test_seed_package_and_free_publication(self):
        self.assertEqual(self.package.price, Decimal('29.90'))
        self.assertEqual(self.package.days, 7)
        response = self.client.post('/api/spaces/', {'title': 'Outra vaga', 'description': 'Disponível', 'price': 300, 'city': 'São Paulo', 'state': 'SP', 'neighborhood': 'Centro', 'address_line': 'Rua 2'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['is_promoted'])
        self.assertFalse(Promotion.objects.exists())

    def test_pending_promotion_cannot_be_self_activated_and_is_idempotent(self):
        first = self.request_promotion()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data['status'], 'pending')
        self.assertEqual(self.request_promotion().status_code, 200)
        self.assertEqual(Promotion.objects.count(), 1)
        self.client.patch(f'/api/spaces/{self.space.pk}/', {'is_promoted': True, 'moderated': False}, format='json')
        self.assertFalse(self.client.get(f'/api/spaces/{self.space.pk}/').data['is_promoted'])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.request_promotion().status_code, 404)

    def test_admin_activation_requires_payment_reference_and_does_not_restart(self):
        self.request_promotion()
        promotion = Promotion.objects.get()
        model_admin = PromotionAdmin(Promotion, admin.site)
        request = RequestFactory().post('/admin/')
        request.user = self.owner
        with patch.object(model_admin, 'message_user'):
            model_admin.activate_paid(request, Promotion.objects.all())
            promotion.refresh_from_db()
            self.assertEqual(promotion.status, 'pending')
            promotion.payment_reference = 'Recibo externo 123'
            promotion.save()
            model_admin.activate_paid(request, Promotion.objects.all())
            promotion.refresh_from_db()
            self.assertEqual(promotion.ends_at - promotion.starts_at, timedelta(days=7))
            ends = promotion.ends_at
            model_admin.activate_paid(request, Promotion.objects.all())
        promotion.refresh_from_db()
        self.assertEqual(promotion.ends_at, ends)
        self.assertTrue(self.client.get(f'/api/spaces/{self.space.pk}/').data['is_promoted'])

    def test_featured_ranking_respects_filters_and_expiry(self):
        other = Space.objects.create(owner=self.owner, title='Mais recente', description='Vaga', price=200, city='Campinas', state='SP', neighborhood='Centro', address_line='Outra rua')
        Promotion.objects.create(space=self.space, package=self.package, price=29.90, days=7, status='active', starts_at=timezone.now()-timedelta(days=1), ends_at=timezone.now()+timedelta(days=6))
        self.assertEqual(self.client.get('/api/spaces/').data['results'][0]['id'], self.space.pk)
        self.assertEqual(self.client.get('/api/spaces/', {'location': 'Campinas'}).data['results'][0]['id'], other.pk)
        self.assertEqual(self.client.get('/api/spaces/', {'max_price': 250}).data['count'], 1)
        Promotion.objects.update(ends_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get('/api/spaces/').data['results'][0]['id'], other.pk)
        self.assertFalse(self.client.get(f'/api/spaces/{self.space.pk}/').data['is_promoted'])

    def test_pending_package_snapshot_and_cancellation(self):
        self.request_promotion()
        self.assertEqual(self.client.delete(f'/api/spaces/{self.space.pk}/').status_code, 400)
        self.assertTrue(Space.objects.filter(pk=self.space.pk).exists())
        self.package.price = 99
        self.package.save()
        self.assertEqual(self.client.get(self.url('promotions')).data[0]['price'], '29.90')
        self.assertEqual(self.client.post(self.url('cancel_promotion')).status_code, 200)
        self.assertEqual(Promotion.objects.get().status, 'cancelled')

    def test_unavailable_and_moderated_listings_cannot_buy_or_receive_contacts(self):
        self.space.availability_status = 'rented'
        self.space.save()
        self.assertEqual(self.request_promotion().status_code, 400)
        self.assertEqual(self.client.get('/api/spaces/').data['count'], 0)
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.client.post(self.url('inquiries'), {'message': 'Olá'}).status_code, 400)
        self.space.moderated = True
        self.space.save()
        self.assertEqual(self.client.get(f'/api/spaces/{self.space.pk}/').status_code, 404)
        self.assertEqual(self.client.post(self.url('event'), {'kind': 'view'}).status_code, 404)

    def test_metrics_are_private_deduplicated_and_exclude_owner(self):
        self.client.post(self.url('event'), {'kind': 'view'})
        self.assertEqual(ListingEvent.objects.count(), 0)
        self.client.force_authenticate(None)
        for _ in range(2):
            self.assertEqual(self.client.post(self.url('event'), {'kind': 'view'}).status_code, 200)
        self.client.post(self.url('event'), {'kind': 'whatsapp'})
        self.assertEqual(ListingEvent.objects.count(), 2)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url('metrics')).status_code, 404)
        self.client.force_authenticate(self.owner)
        metrics = self.client.get(self.url('metrics')).data
        self.assertEqual(metrics['views'], 1)
        self.assertEqual(metrics['whatsapp_clicks'], 1)
        self.assertEqual(metrics['inquiries'], 0)

    def test_inquiries_only_owner_can_read_and_daily_repeat_rejected(self):
        self.client.force_authenticate(self.visitor)
        response = self.client.post(self.url('inquiries'), {'message': 'Posso visitar?', 'reply_phone': '+55 (11) 99999-9999'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Inquiry.objects.get().reply_phone, '5511999999999')
        self.assertEqual(self.client.post(self.url('inquiries'), {'message': 'De novo'}).status_code, 400)
        self.assertEqual(self.client.get(self.url('inquiries')).status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(self.url('inquiries')).data['results'][0]['sender_email'], self.visitor.email)
        self.assertEqual(self.client.post(self.url('inquiries'), {'message': 'Autocontato'}).status_code, 400)

    def test_service_reviews_require_contact_and_are_separate_from_legacy(self):
        self.client.force_authenticate(self.visitor)
        data = {'score': 4, 'comment': 'Respondeu bem'}
        self.assertEqual(self.client.post(self.url('feedback'), data).status_code, 400)
        Inquiry.objects.create(space=self.space, sender=self.visitor, message='Olá')
        self.assertEqual(self.client.post(self.url('feedback'), {'score': 6, 'comment': 'Inválida'}).status_code, 400)
        self.assertEqual(self.client.post(self.url('feedback'), data).status_code, 201)
        self.assertEqual(self.client.post(self.url('feedback'), data).status_code, 400)
        result = self.client.get(f'/api/spaces/{self.space.pk}/')
        self.assertEqual(result.data['rating'], {'average': 4.0, 'count': 1})
        self.assertNotIn('email', self.client.get(self.url('feedback')).data['results'][0])
        ServiceReview.objects.update(is_visible=False)
        self.assertEqual(self.client.get(self.url('feedback')).data['count'], 0)

    def test_former_confirmed_renter_no_longer_receives_private_address(self):
        record = Reservation.objects.create(space=self.space, renter=self.visitor, start_at=timezone.now(), end_at=timezone.now()+timedelta(days=1), status='confirmed', unit_price=400, total_amount=400)
        Review.objects.create(reservation=record, score=5, comment='Antiga')
        self.client.force_authenticate(self.visitor)
        data = self.client.get(f'/api/spaces/{self.space.pk}/').data
        self.assertIsNone(data['exact_address'])
        self.assertEqual(data['rating']['count'], 0)
        self.client.force_authenticate(self.owner)
        self.assertIsNotNone(self.client.get(f'/api/spaces/{self.space.pk}/').data['exact_address'])

    def test_reports_private_and_duplicate_protection(self):
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.client.post(self.url('report'), {'reason': 'duplicate', 'details': 'Outro anúncio igual'}).status_code, 201)
        self.assertEqual(self.client.post(self.url('report'), {'reason': 'fraud', 'details': 'Repetida'}).status_code, 400)
        self.assertEqual(ListingReport.objects.count(), 1)
        self.assertEqual(self.client.get(self.url('report')).status_code, 405)
        self.client.force_authenticate(self.owner)
        payload = {'title': self.space.title, 'description': 'Cópia', 'price': 400, 'city': self.space.city, 'state': 'SP', 'neighborhood': 'Centro', 'address_line': self.space.address_line}
        self.assertEqual(self.client.post('/api/spaces/', payload, format='json').status_code, 400)

    def test_availability_refresh_and_phone_validation(self):
        url = f'/api/spaces/{self.space.pk}/'
        self.assertEqual(self.client.patch(url, {'contact_phone': 'javascript:alert(1)'}).status_code, 400)
        self.assertEqual(self.client.patch(url, {'availability_status': 'negotiating'}).status_code, 200)
        self.space.refresh_from_db()
        old = self.space.availability_checked_at
        self.assertEqual(self.client.post(self.url('refresh')).status_code, 200)
        self.space.refresh_from_db()
        self.assertGreaterEqual(self.space.availability_checked_at, old)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(self.url('refresh')).status_code, 404)

    def test_alert_consent_price_validation_and_ownership(self):
        self.assertEqual(self.client.post('/api/alerts/', {'location': 'Centro'}).status_code, 400)
        self.assertEqual(self.client.post('/api/alerts/', {'location': 'Centro', 'consent': True, 'min_price': 500, 'max_price': 200}, format='json').status_code, 400)
        result = self.client.post('/api/alerts/', {'location': 'Centro', 'consent': True}, format='json')
        self.assertEqual(result.status_code, 201)
        url = f"/api/alerts/{result.data['id']}/"
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/alerts/').data['count'], 0)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {'is_active': False}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_alert_delivery_requires_verified_email_and_respects_pause_and_dedupe(self):
        alert = SavedAlert.objects.create(user=self.visitor, location='Centro', min_price=300, max_price=500)
        SavedAlert.objects.filter(pk=alert.pk).update(created_at=timezone.now()-timedelta(days=1))
        call_command('send_portal_notifications', '--send', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)
        EmailVerification.objects.create(user=self.visitor, email=self.visitor.email, verified_at=timezone.now())
        call_command('send_portal_notifications', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)
        call_command('send_portal_notifications', '--send', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/alertas', mail.outbox[0].body)
        call_command('send_portal_notifications', '--send', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        NotificationDelivery.objects.all().delete()
        alert.is_active = False
        alert.save()
        call_command('send_portal_notifications', '--send', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_inquiry_and_stale_listing_notifications_do_not_repeat(self):
        Inquiry.objects.create(space=self.space, sender=self.visitor, message='Contato')
        Space.objects.filter(pk=self.space.pk).update(availability_checked_at=timezone.now()-timedelta(days=40))
        call_command('send_portal_notifications', '--send', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 2)
        call_command('send_portal_notifications', '--send', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 2)
