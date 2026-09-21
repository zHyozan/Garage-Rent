from django.conf import settings
from django.db import models


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
