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










class PermissionResolver(object):
    RESOLVER_MAP = {
        '$everyone': EveryoneAclResolver,
        '$unauthenticated': UnauthenticatedAclResolver,
        '$authenticated': AuthenticatedAclResolver,
        '$owner': OwnerAclResolver,
        '$admin': AdminAclResolver
    }

    def get_resolver_instance(self, name):
        r_cls = self.RESOLVER_MAP.get(name)
        return r_cls()

    def resolve_permission(self, request=None, property_func=None, model_acl=[], drf={}, obj=None):
        if not model_acl:
            return 'ALLOW'
        resolved = 'ALLOW'

        for acl in model_acl:
            p = acl['property']
            if re.search(p, property_func):
                r = self.get_resolver_instance(acl['principalId'])
                permission = r.get_permission(
                    request=request,
                    drf=drf,
                    obj=obj
                )
                if permission:
                    resolved = acl['permission']

        return resolved
