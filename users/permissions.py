from rest_framework.permissions import BasePermission

from trainings.models import Training
from users.models import Relation


class IsCoachPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user:
            return request.user.is_coach
        return False

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Relation):
            return obj.coach == request.user
        elif isinstance(obj, Training):
            return obj.relation.coach == request.user
        return True
