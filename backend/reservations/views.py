from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Reservation
from .permissions import IsReservationParticipant
from .serializers import ReservationSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsReservationParticipant]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.select_related("space", "space__owner", "renter").filter(
            Q(renter=user) | Q(space__owner=user)
        ).distinct()

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        reservation = self.get_object()
        if reservation.space.owner_id != request.user.id:
            return Response({"detail": "Somente o proprietário pode confirmar."}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status != Reservation.Status.PENDING:
            return Response({"detail": "A reserva não está pendente."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        reservation = self.get_object()
        if reservation.space.owner_id != request.user.id:
            return Response({"detail": "Somente o proprietário pode recusar."}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status != Reservation.Status.PENDING:
            return Response({"detail": "A reserva não está pendente."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = Reservation.Status.REJECTED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if reservation.renter_id != request.user.id:
            return Response({"detail": "Somente o locatário pode cancelar."}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status not in {Reservation.Status.PENDING, Reservation.Status.CONFIRMED}:
            return Response({"detail": "Essa reserva não pode mais ser cancelada."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)
