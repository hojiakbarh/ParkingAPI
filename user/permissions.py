from rest_framework.permissions import BasePermission

from user.models import User


class IsAdmin(BasePermission):
    message = "Siz admin emassiz!"
    def has_permission(self, request, view):
        return request.user.role == User.RoleType.ADMIN.value

