from rest_framework import permissions




class Everyone(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True


#

class EveryoneDeny(permissions.BasePermission):
    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False


#
#
#

class Unauthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return not request.user.is_authenticated

#

class UnauthenticatedDeny(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated


#
#
#


class Authenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated

#

class AuthenticatedDeny(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return not request.user.is_authenticated

#
#
#

class OwnerObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

#

class OwnerObjectDeny(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner != request.user
