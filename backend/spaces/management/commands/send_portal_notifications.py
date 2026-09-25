from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from spaces.models import SavedAlert, Space, Inquiry, NotificationDelivery


class Command(BaseCommand):
    help = 'Alertas consentidos, mensagens e lembretes. Simula por padrão; use --send para enviar. Execute em um único worker.'

    def add_arguments(self, parser):
        parser.add_argument('--send', action='store_true')

    def handle(self, *args, **options):
        self.count = 0
        self.send = options['send']
        now = timezone.now()
        base = settings.FRONTEND_URL
        for alert in SavedAlert.objects.filter(is_active=True).select_related('user'):
            verification = getattr(alert.user, 'email_verification', None)
            if not verification or verification.email.lower() != alert.user.email.lower():
                continue
            matches = Space.objects.filter(is_active=True, moderated=False, created_at__gt=alert.created_at).exclude(availability_status='rented').exclude(owner=alert.user)
            matches = matches.filter(Q(city__icontains=alert.location) | Q(neighborhood__icontains=alert.location))
            if alert.space_type:
                matches = matches.filter(space_type=alert.space_type)
            if alert.billing_period:
                matches = matches.filter(billing_period=alert.billing_period)
            if alert.min_price is not None:
                matches = matches.filter(price__gte=alert.min_price)
            if alert.max_price is not None:
                matches = matches.filter(price__lte=alert.max_price)
            # One digest per alert, not one email per listing.
            fresh = [s for s in matches.order_by('created_at') if not NotificationDelivery.objects.filter(key=f'alert:{alert.pk}:{s.pk}').exists()][:20]
            if fresh:
                body = '\n'.join(f'{s.title} — R$ {s.price}/{s.get_billing_period_display()} — {base}/espacos/{s.pk}' for s in fresh)
                self.deliver([f'alert:{alert.pk}:{s.pk}' for s in fresh], alert.user.email, 'Novos espaços para sua busca', f'{body}\n\nPause ou exclua este alerta: {base}/alertas')
        for inquiry in Inquiry.objects.filter(created_at__gte=now-timedelta(days=7)).select_related('space__owner'):
            self.deliver([f'inquiry:{inquiry.pk}'], inquiry.space.owner.email, 'Novo contato no Garage Rent', f'Você recebeu uma mensagem sobre {inquiry.space.title}. Leia e responda em {base}/meus-anuncios/{inquiry.space_id}/resultados')
        for space in Space.objects.filter(is_active=True, moderated=False, availability_checked_at__lt=now-timedelta(days=30)).exclude(availability_status='rented').select_related('owner'):
            key = f'reminder:{space.pk}:{space.availability_checked_at.date()}:{now.date().isocalendar().year}:{now.date().isocalendar().week}'
            self.deliver([key], space.owner.email, 'Seu espaço continua disponível?', f'Atualize a disponibilidade de {space.title} em {base}/meus-anuncios. Assim, os interessados encontram informações atuais.')
        self.stdout.write(f'{self.count} mensagem(ns) {"enviada(s)" if self.send else "prevista(s); nenhuma enviada (use --send)"}.')

    def deliver(self, keys, email, subject, body):
        if not email or all(NotificationDelivery.objects.filter(key=key).exists() for key in keys):
            return
        if self.send:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            for key in keys:
                NotificationDelivery.objects.get_or_create(key=key)
        self.count += 1
