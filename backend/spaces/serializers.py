from rest_framework import serializers
from .models import Favorite, Space


class SpaceSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    public_location = serializers.CharField(read_only=True)
    exact_address = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = [
            "id", "owner", "space_type", "title", "description", "price", "billing_period",
            "state", "city", "neighborhood", "postal_code", "address_line", "public_location",
            "exact_address", "length_m", "width_m", "height_m", "covered", "electric_gate",
            "security_camera", "access_24h", "lighting", "electricity", "restroom", "cover_image",
            "is_active", "is_favorite", "is_owner", "created_at", "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]
        extra_kwargs = {
            "address_line": {"write_only": True},
            "postal_code": {"write_only": True},
        }

    def get_owner(self, obj):
        return {"id": obj.owner_id, "username": obj.owner.username}

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.id == obj.owner_id)

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, space=obj).exists()

    def get_exact_address(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if request.user.id == obj.owner_id:
            return {"address_line": obj.address_line, "postal_code": obj.postal_code}

        from reservations.models import Reservation
        has_confirmed = Reservation.objects.filter(
            space=obj,
            renter=request.user,
            status=Reservation.Status.CONFIRMED,
        ).exists()
        if has_confirmed:
            return {"address_line": obj.address_line, "postal_code": obj.postal_code}
        return None

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value
