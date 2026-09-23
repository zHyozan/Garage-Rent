from datetime import date, datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Favorite, Space
from .permissions import IsOwnerOrReadOnly
from .serializers import SpaceSerializer
from .location import NearbyQuery, distance_km
from decimal import Decimal, InvalidOperation
from rest_framework.exceptions import ValidationError


class SpaceViewSet(viewsets.ModelViewSet):
    serializer_class = SpaceSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filterset_fields = ["space_type", "billing_period", "city", "state", "covered", "access_24h"]
    search_fields = ["title", "description", "city", "neighborhood"]
    ordering_fields = ["price", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_nearby(self):
        if not hasattr(self, "_nearby"):
            self._nearby = None
            if self.action == "list" and any(key in self.request.query_params for key in ("lat", "lng", "radius")):
                serializer = NearbyQuery(data=self.request.query_params)
                serializer.is_valid(raise_exception=True)
                self._nearby = serializer.validated_data
        return self._nearby

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "nearby": self.get_nearby()}

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        nearby = self.get_nearby()
        if nearby:
            # Filter before pagination. Distance uses only the public coarse region.
            matches = [(s.pk, distance_km(nearby["lat"], nearby["lng"], s.latitude, s.longitude))
                       for s in queryset.exclude(latitude=None).exclude(longitude=None)]
            matches = sorted((pk, d) for pk, d in matches if d <= nearby["radius"])
            queryset = queryset.filter(pk__in=[pk for pk, _ in matches])
            if self.request.query_params.get("ordering") == "distance":
                from django.db.models import Case, When, IntegerField
                ids = [pk for pk, _ in sorted(matches, key=lambda item: item[1])]
                if ids:
                    queryset = queryset.order_by(Case(*[When(pk=pk, then=i) for i, pk in enumerate(ids)], output_field=IntegerField()))
        vehicle = self.request.query_params.get("vehicle")
        if vehicle:
            queryset = queryset.filter(pk__in=[s.pk for s in queryset if vehicle in s.accepted_vehicles])
        return queryset

    def get_queryset(self):
        qs = Space.objects.select_related("owner").prefetch_related("images")
        user = self.request.user
        owner_detail_actions = {"retrieve", "update", "partial_update", "destroy", "availability"}

        if self.action == "mine":
            qs = qs.filter(owner=user)
        elif self.action in owner_detail_actions and user.is_authenticated:
            qs = qs.filter(Q(is_active=True) | Q(owner=user))
        else:
            qs = qs.filter(is_active=True)

        if self.action == "list":
            min_price = self.request.query_params.get("min_price")
            max_price = self.request.query_params.get("max_price")
            try:
                for value in (min_price, max_price):
                    if value and (not Decimal(value).is_finite() or Decimal(value) < 0):
                        raise InvalidOperation
                if min_price and max_price and Decimal(min_price) > Decimal(max_price):
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError("Informe uma faixa de preços válida.")
            location = self.request.query_params.get("location")
            if min_price:
                qs = qs.filter(price__gte=min_price)
            if max_price:
                qs = qs.filter(price__lte=max_price)
            if location:
                qs = qs.filter(Q(city__icontains=location) | Q(neighborhood__icontains=location))

        return qs

    def get_permissions(self):
        if self.action in {"list", "retrieve", "reviews"}:
            return [AllowAny()]
        if self.action in {"mine", "favorites", "favorite"}:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        from reservations.models import Review
        from reservations.serializers import ReviewSerializer
        space = self.get_object()
        queryset = Review.objects.filter(reservation__space=space).select_related("reservation__renter")
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(ReviewSerializer(page, many=True).data)

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        space = self.get_object()
        try:
            start = date.fromisoformat(request.query_params["from"])
            end = date.fromisoformat(request.query_params["to"])
        except (KeyError, ValueError):
            return Response({"detail": "Informe as datas from e to no formato AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if end <= start or end - start > timedelta(days=62):
            return Response({"detail": "O período deve ter de 1 a 62 dias."}, status=status.HTTP_400_BAD_REQUEST)
        start_at = timezone.make_aware(datetime.combine(start, time.min))
        end_at = timezone.make_aware(datetime.combine(end, time.min))
        from reservations.models import Reservation
        occupied = Reservation.objects.filter(
            space=space,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).order_by("start_at").values("start_at", "end_at")
        return Response([{"start_at": item["start_at"], "end_at": item["end_at"]} for item in occupied])

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def mine(self, request):
        queryset = Space.objects.filter(owner=request.user).select_related("owner").prefetch_related("images")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        queryset = Space.objects.filter(favorites__user=request.user, is_active=True).select_related("owner").prefetch_related("images")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        space = self.get_object()
        if request.method == "POST":
            favorite, created = Favorite.objects.get_or_create(user=request.user, space=space)
            return Response({"favorited": True, "created": created}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        Favorite.objects.filter(user=request.user, space=space).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
