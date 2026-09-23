from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Reservation, Review, CANCELLATION_POLICY
from .permissions import IsReservationParticipant
from .serializers import ReservationSerializer, ReviewSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsReservationParticipant]
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=False, methods=["post"])
    def quote(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attrs = serializer.validated_data
        occupied = Reservation.objects.filter(space=attrs["space"], status__in=["pending", "confirmed"], start_at__lt=attrs["end_at"], end_at__gt=attrs["start_at"]).exists()
        if occupied:
            return Response({"detail": "Este período já está ocupado. Escolha outras datas."}, status=400)
        reservation = Reservation(space=attrs["space"], start_at=attrs["start_at"], end_at=attrs["end_at"], renter=request.user)
        return Response({"total_amount": str(reservation.calculate_total()), "unit_price": str(attrs["space"].price), "billing_period": attrs["space"].billing_period, "cancellation_policy": CANCELLATION_POLICY, "detail": "Disponibilidade verificada agora; a solicitação será validada novamente ao enviar."})

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def complete(self, request, pk=None):
        reservation = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if reservation.status != Reservation.Status.CONFIRMED or reservation.end_at > timezone.now():
            return Response({"detail": "Somente reservas confirmadas e com período encerrado podem ser concluídas."}, status=400)
        reservation.status = Reservation.Status.COMPLETED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def review(self, request, pk=None):
        reservation = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if reservation.renter_id != request.user.id:
            return Response({"detail": "Somente o locatário pode avaliar."}, status=403)
        if reservation.status != Reservation.Status.COMPLETED or reservation.end_at > timezone.now():
            return Response({"detail": "Conclua uma reserva encerrada antes de avaliar."}, status=400)
        if Review.objects.filter(reservation=reservation).exists():
            return Response({"detail": "Esta reserva já foi avaliada."}, status=400)
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(reservation=reservation)
        return Response(serializer.data, status=201)

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.select_related("space", "space__owner", "renter").filter(
            Q(renter=user) | Q(space__owner=user)
        ).distinct()

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirm(self, request, pk=None):
        reservation = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if reservation.space.owner_id != request.user.id:
            return Response({"detail": "Somente o proprietário pode confirmar."}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status != Reservation.Status.PENDING:
            return Response({"detail": "A reserva não está pendente."}, status=status.HTTP_400_BAD_REQUEST)
        if reservation.start_at <= timezone.now():
            return Response({"detail": "O início desta reserva já passou."}, status=400)
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        reservation = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if reservation.space.owner_id != request.user.id:
            return Response({"detail": "Somente o proprietário pode recusar."}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status != Reservation.Status.PENDING:
            return Response({"detail": "A reserva não está pendente."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = Reservation.Status.REJECTED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        reservation = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if reservation.renter_id != request.user.id:
            return Response({"detail": "Somente o locatário pode cancelar."}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status not in {Reservation.Status.PENDING, Reservation.Status.CONFIRMED}:
            return Response({"detail": "Essa reserva não pode mais ser cancelada."}, status=status.HTTP_400_BAD_REQUEST)
        if reservation.start_at <= timezone.now():
            return Response({"detail": "O prazo de cancelamento terminou no início da reserva."}, status=400)
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)
