from django.contrib import admin
from .models import Favorite, Space
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from .models import PromotionPackage, Promotion, ListingReport, ServiceReview, Inquiry, SavedAlert


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ("title", "space_type", "owner", "city", "state", "price", "billing_period", "availability_status", "is_active", "moderated")
    list_filter = ("space_type", "billing_period", "state", "is_active", "moderated", "availability_status")
    search_fields = ("title", "city", "neighborhood", "owner__username")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "space", "created_at")


@admin.register(PromotionPackage)
class PromotionPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'days', 'is_active')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('id', 'space', 'price', 'days', 'status', 'ends_at')
    list_filter = ('status',)
    readonly_fields = ('space', 'package', 'price', 'days', 'status', 'activated_by', 'starts_at', 'ends_at', 'created_at')
    actions = ['activate_paid', 'cancel']

    def has_add_permission(self, request):
        return False

    @admin.action(description='Confirmar pagamento externo e ativar destaque')
    def activate_paid(self, request, queryset):
        count = 0
        with transaction.atomic():
            for p in queryset.select_for_update().select_related('space'):
                if p.status != 'pending' or not p.payment_reference.strip() or not p.space.is_active or p.space.moderated or p.space.availability_status == 'rented':
                    continue
                now = timezone.now()
                if p.space.promotions.filter(status='active', ends_at__gt=now).exists():
                    continue
                p.status, p.starts_at, p.ends_at, p.activated_by = 'active', now, now+timedelta(days=p.days), request.user
                p.save(update_fields=['status', 'starts_at', 'ends_at', 'activated_by'])
                count += 1
        self.message_user(request, f'{count} destaque(s) ativado(s). É obrigatório salvar a referência do pagamento e manter o anúncio disponível antes de ativar.', messages.INFO)

    @admin.action(description='Cancelar destaque (não realiza reembolso)')
    def cancel(self, request, queryset):
        queryset.update(status='cancelled')


@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = ('space', 'reason', 'resolved', 'created_at')
    list_filter = ('resolved', 'reason')
    readonly_fields = ('space', 'reporter', 'reason', 'details', 'created_at')
    actions = ['hide_listing']

    @admin.action(description='Ocultar anúncios denunciados e marcar denúncias resolvidas')
    def hide_listing(self, request, queryset):
        Space.objects.filter(pk__in=queryset.values('space_id')).update(moderated=True)
        queryset.update(resolved=True)


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ('space', 'author', 'score', 'is_visible', 'created_at')
    list_filter = ('is_visible',)
    readonly_fields = ('space', 'author', 'score', 'comment', 'created_at')


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('space', 'sender', 'created_at')
    readonly_fields = ('space', 'sender', 'message', 'reply_phone', 'created_at')


@admin.register(SavedAlert)
class SavedAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'is_active', 'consent_at')
    readonly_fields = ('user', 'location', 'space_type', 'billing_period', 'min_price', 'max_price', 'consent_at', 'created_at')
