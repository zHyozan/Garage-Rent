from rest_framework.permissions import BasePermission


class IsReservationParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
            obj.renter_id == request.user.id or obj.space.owner_id == request.user.id
        )
