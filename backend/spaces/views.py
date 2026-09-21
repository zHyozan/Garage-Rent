from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Favorite, Space
from .permissions import IsOwnerOrReadOnly
from .serializers import SpaceSerializer


class SpaceViewSet(viewsets.ModelViewSet):
    serializer_class = SpaceSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filterset_fields = ["space_type", "billing_period", "city", "state", "covered", "access_24h"]
    search_fields = ["title", "description", "city", "neighborhood"]
    ordering_fields = ["price", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Space.objects.select_related("owner").prefetch_related("images")
        user = self.request.user
        owner_detail_actions = {"retrieve", "update", "partial_update", "destroy"}

        if self.action == "mine":
            qs = qs.filter(owner=user)
        elif self.action in owner_detail_actions and user.is_authenticated:
            qs = qs.filter(Q(is_active=True) | Q(owner=user))
        else:
            qs = qs.filter(is_active=True)

        if self.action == "list":
            min_price = self.request.query_params.get("min_price")
            max_price = self.request.query_params.get("max_price")
            location = self.request.query_params.get("location")
            if min_price:
                qs = qs.filter(price__gte=min_price)
            if max_price:
                qs = qs.filter(price__lte=max_price)
            if location:
                qs = qs.filter(Q(city__icontains=location) | Q(neighborhood__icontains=location))

        return qs

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        if self.action in {"mine", "favorites", "favorite"}:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

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
