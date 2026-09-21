from django.contrib import admin
from .models import Favorite, Space


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ("title", "space_type", "owner", "city", "state", "price", "billing_period", "is_active")
    list_filter = ("space_type", "billing_period", "state", "is_active")
    search_fields = ("title", "city", "neighborhood", "owner__username")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "space", "created_at")
