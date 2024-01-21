from rest_framework import permissions


class IsMeteorologist(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.user_role == 'meteorologist'))


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.user_role == 'r_manager' or request.user.user_role == 'r_admin'))


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_role == 'r_admin')


class ManagerOrMeteo(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.user_role == 'r_manager' or request.user.user_role == 'r_admin' or request.user.user_role == 'meteorologist'))
