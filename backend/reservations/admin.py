from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "space", "renter", "start_at", "end_at", "status", "total_amount")
    list_filter = ("status", "space__space_type")
    search_fields = ("space__title", "renter__username", "space__owner__username")
