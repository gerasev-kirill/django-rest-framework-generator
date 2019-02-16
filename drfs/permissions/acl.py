import six



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
            if isinstance(obj.owner, six.integer_types) or isinstance(obj.owner, six.text_type) or isinstance(obj.owner, six.string_types):
                return obj.owner == request.user.id
            return obj.owner == request.user

        from django.contrib.auth import get_user_model
        UserModel = get_user_model()

        if isinstance(obj, UserModel):
            return obj == request.user
        return False


class AdminAclResolver(AclResolver):
    def get_permission(self, request=None, drf={}, **kwargs):
        is_superuser = getattr(request.user, 'is_superuser', False)
        is_staff = getattr(request.user, 'is_staff', False)
        is_admin = getattr(request.user, 'userRole', None) in ['a', 'admin']
        return is_staff or is_superuser or is_admin
