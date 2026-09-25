from django.db import transaction
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers
from .models import Favorite, Space, SpaceImage
from .location import distance_km


class SpaceSerializer(serializers.ModelSerializer):
    contact_phone = serializers.CharField(max_length=24, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=-90, max_value=90, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=-180, max_value=180, required=False, allow_null=True)
    distance_km = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    is_promoted = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    public_location = serializers.CharField(read_only=True)
    exact_address = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    images_upload = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    remove_image_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    gallery_order = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Space
        fields = [
            "id", "owner", "space_type", "title", "description", "price", "billing_period",
            "state", "city", "neighborhood", "postal_code", "address_line", "public_location",
            "exact_address", "length_m", "width_m", "height_m", "covered", "electric_gate",
            "security_camera", "access_24h", "lighting", "electricity", "restroom", "cover_image",
            "images", "images_upload", "remove_image_ids", "gallery_order",
            "is_active", "is_favorite", "is_owner", "created_at", "updated_at",
            "latitude", "longitude", "accepted_vehicles", "distance_km", "rating",
            "contact_phone", "whatsapp_enabled", "availability_status", "availability_checked_at", "is_promoted", "moderated",
        ]
        read_only_fields = ["owner", "created_at", "updated_at", "availability_checked_at", "moderated"]
        extra_kwargs = {
            "address_line": {"write_only": True},
            "postal_code": {"write_only": True},
        }

    def get_owner(self, obj):
        verification = getattr(obj.owner, "email_verification", None)
        return {"id": obj.owner_id, "username": obj.owner.username, "email_verified": bool(verification and verification.email.lower() == obj.owner.email.lower())}

    def get_distance_km(self, obj):
        nearby = self.context.get("nearby")
        if nearby and obj.latitude is not None and obj.longitude is not None:
            return round(distance_km(nearby["lat"], nearby["lng"], obj.latitude, obj.longitude), 1)
        return None

    def get_is_promoted(self, obj):
        from django.utils import timezone
        return obj.is_active and not obj.moderated and obj.availability_status != "rented" and obj.promotions.filter(status="active", starts_at__lte=timezone.now(), ends_at__gt=timezone.now()).exists()

    def get_rating(self, obj):
        from django.db.models import Avg, Count
        result = obj.service_reviews.filter(is_visible=True).aggregate(average=Avg("score"), count=Count("id"))
        if result["average"] is not None:
            result["average"] = round(result["average"], 1)
        return result

    def validate_contact_phone(self, value):
        from .portal import phone_number
        return phone_number(value)

    def validate_accepted_vehicles(self, value):
        allowed = {"motorcycle", "car", "suv", "van", "truck", "bicycle"}
        if not isinstance(value, list) or any(not isinstance(v, str) or v not in allowed for v in value) or len(value) != len(set(value)):
            raise serializers.ValidationError("Selecione tipos de veículos válidos, sem repetições.")
        return value

    def get_images(self, obj):
        request = self.context.get("request")
        images = [{"id": image.id, "url": request.build_absolute_uri(image.image.url) if request else image.image.url} for image in obj.images.all()]
        if obj.cover_image:
            legacy = request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
            images.insert(0, {"id": None, "url": legacy})
        return images

    def get_cover_image(self, obj):
        images = self.get_images(obj)
        return images[0]["url"] if images else None

    def validate_images_upload(self, uploads):
        for image in uploads:
            if image.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Cada imagem deve ter no máximo 5 MB.")
            try:
                image.seek(0)
                image_format = Image.open(image).format
                image.seek(0)
            except (UnidentifiedImageError, OSError):
                raise serializers.ValidationError("Envie imagens JPEG, PNG ou WebP válidas.")
            if image_format not in {"JPEG", "PNG", "WEBP"}:
                raise serializers.ValidationError("Envie imagens JPEG, PNG ou WebP.")
        return uploads

    def validate(self, attrs):
        lat = attrs.get("latitude", getattr(self.instance, "latitude", None))
        lng = attrs.get("longitude", getattr(self.instance, "longitude", None))
        if (lat is None) != (lng is None):
            raise serializers.ValidationError("Informe latitude e longitude juntas.")
        for field in ("length_m", "width_m", "height_m"):
            if attrs.get(field) is not None and attrs[field] <= 0:
                raise serializers.ValidationError({field: "A dimensão deve ser maior que zero."})
        title = attrs.get("title", getattr(self.instance, "title", ""))
        address = attrs.get("address_line", getattr(self.instance, "address_line", ""))
        city = attrs.get("city", getattr(self.instance, "city", ""))
        owner = self.context["request"].user
        duplicates = Space.objects.filter(owner=owner, title__iexact=title.strip(), address_line__iexact=address.strip(), city__iexact=city.strip(), is_active=True)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if (not self.instance or any(key in attrs for key in ("title", "address_line", "city", "is_active"))) and attrs.get("is_active", getattr(self.instance, "is_active", True)) and duplicates.exists():
            raise serializers.ValidationError("Você já possui um anúncio ativo com este título e endereço. Edite o existente ou identifique a vaga diferente no título.")
        uploads = attrs.get("images_upload", [])
        removed = attrs.get("remove_image_ids", [])
        order = attrs.get("gallery_order")
        if self.instance:
            existing_ids = list(self.instance.images.values_list("id", flat=True))
            if len(removed) != len(set(removed)) or not set(removed).issubset(existing_ids):
                raise serializers.ValidationError({"remove_image_ids": "Seleção de imagens inválida."})
            remaining = set(existing_ids) - set(removed)
            expected_order = {f"old:{image_id}" for image_id in remaining}
            expected_order.update(f"new:{index}" for index in range(len(uploads)))
            if order is not None and (len(order) != len(expected_order) or set(order) != expected_order):
                raise serializers.ValidationError({"gallery_order": "A ordem deve conter todas as imagens mantidas e novas."})
            existing = len(remaining) + bool(self.instance.cover_image)
        else:
            expected_order = {f"new:{index}" for index in range(len(uploads))}
            if removed or (order is not None and (len(order) != len(expected_order) or set(order) != expected_order)):
                raise serializers.ValidationError({"gallery_order": "Ordem das imagens inválida."})
            existing = 0
        if existing + len(uploads) > 8:
            raise serializers.ValidationError({"images_upload": "O anúncio pode ter no máximo 8 imagens."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        uploads = validated_data.pop("images_upload", [])
        validated_data.pop("remove_image_ids", None)
        order = validated_data.pop("gallery_order", None)
        space = super().create(validated_data)
        order = order if order is not None else [f"new:{index}" for index in range(len(uploads))]
        SpaceImage.objects.bulk_create([
            SpaceImage(space=space, image=uploads[int(key.split(":")[1])], position=position)
            for position, key in enumerate(order)
        ])
        return space

    @transaction.atomic
    def update(self, instance, validated_data):
        uploads = validated_data.pop("images_upload", [])
        removed = validated_data.pop("remove_image_ids", [])
        order = validated_data.pop("gallery_order", None)
        if "availability_status" in validated_data:
            from django.utils import timezone
            validated_data["availability_checked_at"] = timezone.now()
        space = super().update(instance, validated_data)
        for image in space.images.filter(id__in=removed):
            storage, name = image.image.storage, image.image.name
            image.delete()
            transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))
        if hasattr(space, "_prefetched_objects_cache"):
            space._prefetched_objects_cache.pop("images", None)
        remaining = list(space.images.all())
        if order is None:
            order = [f"old:{image.id}" for image in remaining] + [f"new:{index}" for index in range(len(uploads))]
        new_images = []
        for position, key in enumerate(order):
            kind, index = key.split(":")
            if kind == "old":
                SpaceImage.objects.filter(space=space, id=int(index)).update(position=position)
            else:
                new_images.append(SpaceImage(space=space, image=uploads[int(index)], position=position))
        SpaceImage.objects.bulk_create(new_images)
        if hasattr(space, "_prefetched_objects_cache"):
            space._prefetched_objects_cache.pop("images", None)
        return space

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

        return None

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value
