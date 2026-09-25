from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Reservation
from .serializers import ReservationSerializer


class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    """Historical records only. Classified listings no longer create reservations."""
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = []

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.select_related("space", "space__owner", "renter").filter(
            Q(renter=user) | Q(space__owner=user)
        ).distinct()
