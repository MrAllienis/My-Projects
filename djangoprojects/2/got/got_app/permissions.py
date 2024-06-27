from rest_framework import permissions

class AllForAdminOtherReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if 'admin' in request.user.username:
            return True
        elif request.method in permissions.SAFE_METHODS:
            return True
