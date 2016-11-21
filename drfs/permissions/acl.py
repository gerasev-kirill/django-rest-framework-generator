import re








class AclResolver(object):
    def get_permission(self, request=None, drf={}, **kwargs):
        pass


class EveryoneAclResolver(AclResolver):
    def get_permission(self, request=None, drf={}, **kwargs):
        return True


class UnauthenticatedAclResolver(AclResolver):
    def get_permission(self, request=None, drf={}, **kwargs):
        is_authenticated = request.user.is_authenticated()
        return not is_authenticated


class AuthenticatedAclResolver(AclResolver):
    def get_permission(self, request=None, drf={}, **kwargs):
        return request.user.is_authenticated()


class OwnerAclResolver(AclResolver):
    def get_permission(self, request=None, drf={}, obj=None, **kwargs):
        if not request.user.is_authenticated():
            return False
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        from django.contrib.auth.models import User
        if isinstance(obj, User):
            return obj == request.user
        return False


class AdminAclResolver(AclResolver):
    def get_permission(self, request=None, drf={}, **kwargs):
        return request.user and getattr(request.user, 'is_staff', False)
