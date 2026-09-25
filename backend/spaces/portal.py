import re
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .models import (Space, PromotionPackage, Promotion, ListingEvent, Inquiry,
                     ServiceReview, ListingReport, SavedAlert)


def phone_number(value):
    digits = re.sub(r"[\s()+.-]", "", value)
    if digits and not re.fullmatch(r"55[1-9]\d{9,10}", digits):
        raise serializers.ValidationError("Informe telefone brasileiro com 55, DDD e número, por exemplo 5511999999999.")
    return digits


class PortalUserThrottle(UserRateThrottle):
    rate = '60/hour'
    scope = 'portal_user'


class PortalAnonThrottle(AnonRateThrottle):
    rate = '120/hour'
    scope = 'portal_anon'


class InquirySerializer(serializers.ModelSerializer):
    reply_phone = serializers.CharField(max_length=24, required=False, allow_blank=True)
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    space_title = serializers.CharField(source='space.title', read_only=True)

    class Meta:
        model = Inquiry
        fields = ['id', 'space', 'space_title', 'sender_name', 'sender_email', 'message', 'reply_phone', 'created_at']
        read_only_fields = ['space', 'created_at']

    def validate_reply_phone(self, value):
        return phone_number(value)


class ServiceReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    score = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = ServiceReview
        fields = ['id', 'author_name', 'score', 'comment', 'created_at']
        read_only_fields = ['created_at']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingReport
        fields = ['reason', 'details']


class AlertSerializer(serializers.ModelSerializer):
    consent = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = SavedAlert
        fields = ['id', 'location', 'space_type', 'billing_period', 'min_price', 'max_price', 'is_active', 'consent', 'consent_at', 'created_at']
        read_only_fields = ['consent_at', 'created_at']

    def validate(self, attrs):
        if not self.instance and attrs.pop('consent', False) is not True:
            raise serializers.ValidationError('Autorize o recebimento dos alertas por e-mail.')
        attrs.pop('consent', None)
        lo = attrs.get('min_price', getattr(self.instance, 'min_price', None))
        hi = attrs.get('max_price', getattr(self.instance, 'max_price', None))
        if (lo is not None and lo < 0) or (hi is not None and hi < 0) or (lo is not None and hi is not None and lo > hi):
            raise serializers.ValidationError('Informe uma faixa de preços válida.')
        return attrs


class SavedAlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filter_backends = []

    def get_queryset(self):
        return SavedAlert.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        if self.get_queryset().count() >= 20:
            raise ValidationError('Limite de 20 alertas. Exclua um alerta antes de criar outro.')
        serializer.save(user=self.request.user)


def promotion_data(p):
    return {'id': p.pk, 'space': p.space_id, 'price': str(p.price), 'days': p.days,
            'instructions': p.instructions, 'status': 'expired' if p.status == 'active' and p.ends_at and p.ends_at <= timezone.now() else p.status,
            'starts_at': p.starts_at, 'ends_at': p.ends_at, 'created_at': p.created_at}


class PortalViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PortalUserThrottle, PortalAnonThrottle]
    filter_backends = []

    def public_space(self, pk):
        return get_object_or_404(Space, pk=pk, is_active=True, moderated=False)

    def owner_space(self, pk):
        return get_object_or_404(Space, pk=pk, owner=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def packages(self, request):
        return Response(list(PromotionPackage.objects.filter(is_active=True).values('id', 'name', 'price', 'days', 'instructions')))

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def event(self, request, pk=None):
        space = self.public_space(pk)
        kind = request.data.get('kind')
        if kind not in {'view', 'whatsapp', 'phone'}:
            raise ValidationError('Evento inválido.')
        if kind != 'view' and (not space.contact_phone or space.availability_status == 'rented' or (kind == 'whatsapp' and not space.whatsapp_enabled)):
            raise ValidationError('Contato indisponível.')
        if request.user.is_authenticated and request.user.pk == space.owner_id:
            return Response({'recorded': False})
        identity = f'user:{request.user.pk}' if request.user.is_authenticated else f"ip:{request.META.get('REMOTE_ADDR', '')}:{request.META.get('HTTP_USER_AGENT', '')[:200]}"
        visitor = salted_hmac('listing-event', f'{timezone.localdate()}:{identity}').hexdigest()
        _, created = ListingEvent.objects.get_or_create(space=space, kind=kind, visitor_hash=visitor, day=timezone.localdate())
        return Response({'recorded': created})

    @action(detail=True, methods=['get', 'post'])
    def inquiries(self, request, pk=None):
        if request.method == 'GET':
            space = self.owner_space(pk)
            rows = space.inquiries.select_related('sender').order_by('-created_at')
            return self.get_paginated_response(InquirySerializer(self.paginate_queryset(rows), many=True).data)
        space = self.public_space(pk)
        if space.owner_id == request.user.pk or space.availability_status == 'rented':
            raise ValidationError('Este anúncio não recebe seu contato.')
        if Inquiry.objects.filter(space=space, sender=request.user, created_at__gte=timezone.now()-timedelta(hours=24)).exists():
            raise ValidationError('Você já enviou uma mensagem para este anúncio nas últimas 24 horas.')
        serializer = InquirySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(space=space, sender=request.user)
        return Response({'detail': 'Mensagem enviada. O anunciante poderá responder pelo e-mail da sua conta ou telefone informado.'}, status=201)

    @action(detail=True, methods=['get', 'post'], permission_classes=[AllowAny])
    def feedback(self, request, pk=None):
        space = self.public_space(pk)
        if request.method == 'GET':
            rows = space.service_reviews.filter(is_visible=True).select_related('author').order_by('-created_at')
            return self.get_paginated_response(ServiceReviewSerializer(self.paginate_queryset(rows), many=True).data)
        if not request.user.is_authenticated:
            return Response({'detail': 'Entre para avaliar o atendimento.'}, status=401)
        if not Inquiry.objects.filter(space=space, sender=request.user).exists():
            raise ValidationError('Envie uma mensagem pelo formulário antes de avaliar o atendimento. A locação não é verificada pelo site.')
        serializer = ServiceReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, created = ServiceReview.objects.get_or_create(space=space, author=request.user, defaults=serializer.validated_data)
        if not created:
            raise ValidationError('Você já avaliou o atendimento deste anúncio.')
        return Response({'detail': 'Avaliação de atendimento publicada.'}, status=201)

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        space = self.public_space(pk)
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if ListingReport.objects.filter(space=space, reporter=request.user, resolved=False).exists():
            raise ValidationError('Sua denúncia já está em análise.')
        serializer.save(space=space, reporter=request.user)
        return Response({'detail': 'Denúncia recebida para análise. Seus dados não serão exibidos ao anunciante.'}, status=201)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        space = self.owner_space(pk)
        since = timezone.localdate()-timedelta(days=29)
        counts = {x['kind']: x['total'] for x in space.events.filter(day__gte=since).values('kind').annotate(total=Count('id'))}
        return Response({'views': counts.get('view', 0), 'whatsapp_clicks': counts.get('whatsapp', 0), 'phone_clicks': counts.get('phone', 0),
                         'inquiries': space.inquiries.filter(created_at__date__gte=since).count(), 'days': 30})

    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        space = self.owner_space(pk)
        space.availability_checked_at = timezone.now()
        space.save(update_fields=['availability_checked_at'])
        return Response({'detail': 'Disponibilidade revisada hoje.'})

    @action(detail=True, methods=['get', 'post'])
    def promotions(self, request, pk=None):
        space = self.owner_space(pk)
        if request.method == 'GET':
            return Response([promotion_data(p) for p in space.promotions.order_by('-created_at')])
        if not space.is_active or space.moderated or space.availability_status == 'rented':
            raise ValidationError('Ative um anúncio disponível e aprovado pela moderação antes de solicitar destaque.')
        package_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('package'))
        package = get_object_or_404(PromotionPackage, pk=package_id, is_active=True)
        with transaction.atomic():
            Space.objects.select_for_update().get(pk=space.pk)
            if space.promotions.filter(status='active', ends_at__gt=timezone.now()).exists():
                raise ValidationError('Este anúncio já possui destaque vigente.')
            p, created = Promotion.objects.get_or_create(space=space, status='pending', defaults={'package': package, 'price': package.price, 'days': package.days, 'instructions': package.instructions})
        return Response(promotion_data(p), status=201 if created else 200)

    @action(detail=True, methods=['post'])
    def cancel_promotion(self, request, pk=None):
        space = self.owner_space(pk)
        space.promotions.filter(status='pending').update(status='cancelled')
        return Response({'detail': 'Solicitação pendente cancelada. Se já pagou, contate a administração para conciliação.'})
