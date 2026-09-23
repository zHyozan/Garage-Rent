import math
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from spaces.models import Space

CANCELLATION_POLICY = "Cancelamento sem cobrança pela plataforma até o início da reserva. Após o início, combine qualquer alteração com o proprietário. Não há pagamento on-line nesta versão."


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        CONFIRMED = "confirmed", "Confirmada"
        REJECTED = "rejected", "Recusada"
        CANCELLED = "cancelled", "Cancelada"
        COMPLETED = "completed", "Concluída"

    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="reservations")
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["space", "start_at", "end_at"]),
            models.Index(fields=["renter", "status"]),
        ]

    def __str__(self):
        return f"Reserva #{self.pk or 'nova'} - {self.space}"

    def clean(self):
        if self.end_at <= self.start_at:
            raise ValidationError("A data final deve ser posterior à data inicial.")
        if self.renter_id and self.space_id and self.renter_id == self.space.owner_id:
            raise ValidationError("O proprietário não pode reservar o próprio espaço.")

    def calculate_total(self):
        seconds = max((self.end_at - self.start_at).total_seconds(), 1)
        if self.space.billing_period == Space.BillingPeriod.HOUR:
            units = math.ceil(seconds / 3600)
        elif self.space.billing_period == Space.BillingPeriod.DAY:
            units = math.ceil(seconds / 86400)
        else:
            days = math.ceil(seconds / 86400)
            units = math.ceil(days / 30)
        return (Decimal(units) * self.space.price).quantize(Decimal("0.01"))


class Review(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name="review")
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=5), name="review_score_1_to_5")]
