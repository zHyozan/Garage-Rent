from django.conf import settings
from django.db import models
from django.utils import timezone


class Space(models.Model):
    class SpaceType(models.TextChoices):
        GARAGE = "garage", "Garagem"
        PARKING = "parking", "Vaga"
        WAREHOUSE = "warehouse", "Galpão"

    class BillingPeriod(models.TextChoices):
        HOUR = "hour", "Hora"
        DAY = "day", "Dia"
        MONTH = "month", "Mês"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="spaces")
    space_type = models.CharField(max_length=20, choices=SpaceType.choices, default=SpaceType.GARAGE)
    title = models.CharField(max_length=120)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_period = models.CharField(max_length=10, choices=BillingPeriod.choices, default=BillingPeriod.MONTH)

    state = models.CharField(max_length=2)
    city = models.CharField(max_length=80)
    neighborhood = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=12, blank=True)
    address_line = models.CharField(max_length=180, help_text="Endereço exato, não exibido publicamente.")
    # Only a coarse region is stored, never precise GPS coordinates.
    latitude = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    longitude = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accepted_vehicles = models.JSONField(default=list, blank=True)

    length_m = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_m = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_m = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    covered = models.BooleanField(default=False)
    electric_gate = models.BooleanField(default=False)
    security_camera = models.BooleanField(default=False)
    access_24h = models.BooleanField(default=False)
    lighting = models.BooleanField(default=False)
    electricity = models.BooleanField(default=False)
    restroom = models.BooleanField(default=False)

    cover_image = models.ImageField(upload_to="spaces/%Y/%m/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    availability_status = models.CharField(max_length=16, choices=[("available", "Disponível"), ("negotiating", "Em negociação"), ("rented", "Alugado")], default="available")
    contact_phone = models.CharField(max_length=16, blank=True)
    whatsapp_enabled = models.BooleanField(default=True)
    moderated = models.BooleanField(default=False, help_text="Oculta o anúncio por decisão da moderação.")
    availability_checked_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city", "state"]),
            models.Index(fields=["space_type", "is_active"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return self.title

    @property
    def public_location(self):
        return f"{self.neighborhood}, {self.city} - {self.state.upper()}"


class SpaceImage(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="spaces/%Y/%m/")
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_spaces")
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "space"], name="unique_user_space_favorite")
        ]

    def __str__(self):
        return f"{self.user} -> {self.space}"


class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verification")
    email = models.EmailField()
    verified_at = models.DateTimeField()


class PromotionPackage(models.Model):
    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    days = models.PositiveSmallIntegerField(default=7)
    instructions = models.TextField(help_text="Instruções de cobrança externa. Não inclua dados de clientes.")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0, days__gt=0), name="positive_promotion_package")]

    def __str__(self):
        return f"{self.name} — R$ {self.price} / {self.days} dias"


class Promotion(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="promotions")
    package = models.ForeignKey(PromotionPackage, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    days = models.PositiveSmallIntegerField()
    instructions = models.TextField()
    status = models.CharField(max_length=12, choices=[("pending", "Aguardando pagamento externo"), ("active", "Ativado"), ("cancelled", "Cancelado")], default="pending")
    payment_reference = models.CharField(max_length=120, blank=True, help_text="Referência conferida pela administração; não armazene dados bancários sensíveis.")
    activated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["space"], condition=models.Q(status="pending"), name="one_pending_promotion_per_space")]


class ListingEvent(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=12, choices=[("view", "Visualização"), ("whatsapp", "Clique WhatsApp"), ("phone", "Clique telefone")])
    visitor_hash = models.CharField(max_length=64)
    day = models.DateField(default=timezone.localdate)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["space", "kind", "visitor_hash", "day"], name="daily_listing_event")]


class Inquiry(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="inquiries")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(max_length=2000)
    reply_phone = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ServiceReview(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="service_reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(max_length=1000)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["space", "author"], name="one_service_review_per_author"), models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=5), name="service_review_score")]


class ListingReport(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=[("fraud", "Suspeita de fraude"), ("duplicate", "Anúncio duplicado"), ("unavailable", "Indisponível"), ("other", "Outro")])
    details = models.TextField(max_length=1000)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class SavedAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    space_type = models.CharField(max_length=20, choices=Space.SpaceType.choices, blank=True)
    billing_period = models.CharField(max_length=10, choices=Space.BillingPeriod.choices, blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    consent_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class NotificationDelivery(models.Model):
    key = models.CharField(max_length=160, unique=True)
    sent_at = models.DateTimeField(auto_now_add=True)
