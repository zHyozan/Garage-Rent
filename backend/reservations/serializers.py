from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from spaces.models import Space
from .models import Reservation, Review, CANCELLATION_POLICY


class ReviewSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(min_value=1, max_value=5)
    author = serializers.CharField(source="reservation.renter.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "score", "comment", "author", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReservationSerializer(serializers.ModelSerializer):
    expected_total = serializers.DecimalField(max_digits=12, decimal_places=2, write_only=True, required=False)
    review = ReviewSerializer(read_only=True)
    cancellation_policy = serializers.SerializerMethodField()
    renter = serializers.SerializerMethodField()
    space_summary = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            "id", "space", "space_summary", "renter", "start_at", "end_at", "status",
            "unit_price", "total_amount", "created_at", "updated_at",
            "review", "cancellation_policy",
            "expected_total",
        ]
        read_only_fields = ["renter", "status", "unit_price", "total_amount", "created_at", "updated_at"]

    def get_cancellation_policy(self, obj):
        return CANCELLATION_POLICY

    def get_renter(self, obj):
        return {"id": obj.renter_id, "username": obj.renter.username}

    def get_space_summary(self, obj):
        first_image = obj.space.images.first()
        return {
            "id": obj.space_id,
            "title": obj.space.title,
            "public_location": obj.space.public_location,
            "owner_id": obj.space.owner_id,
            "cover_image": obj.space.cover_image.url if obj.space.cover_image else (first_image.image.url if first_image else None),
        }

    def validate(self, attrs):
        request = self.context["request"]
        space = attrs["space"]
        start_at = attrs["start_at"]
        end_at = attrs["end_at"]

        if space.owner_id == request.user.id:
            raise serializers.ValidationError("Você não pode reservar o próprio espaço.")
        if not space.is_active:
            raise serializers.ValidationError("Este espaço não está disponível.")
        if start_at >= end_at:
            raise serializers.ValidationError("A data final deve ser posterior à data inicial.")
        if start_at < timezone.now():
            raise serializers.ValidationError("A reserva não pode começar no passado.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        space = Space.objects.select_for_update().get(pk=validated_data["space"].pk)
        if not space.is_active or space.owner_id == request.user.id:
            raise serializers.ValidationError("Este espaço não está disponível para reserva.")
        start_at = validated_data["start_at"]
        end_at = validated_data["end_at"]

        overlap = Reservation.objects.filter(
            space=space,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).exists()
        if overlap:
            raise serializers.ValidationError("Já existe uma reserva pendente ou confirmada nesse período.")

        reservation = Reservation(
            space=space,
            renter=request.user,
            start_at=start_at,
            end_at=end_at,
            unit_price=space.price,
            total_amount=0,
        )
        reservation.full_clean(exclude=["total_amount"])
        reservation.total_amount = reservation.calculate_total()
        expected = validated_data.get("expected_total")
        if expected is not None and expected != reservation.total_amount:
            raise serializers.ValidationError("O preço mudou. Consulte o total novamente antes de confirmar.")
        reservation.save()
        return reservation
