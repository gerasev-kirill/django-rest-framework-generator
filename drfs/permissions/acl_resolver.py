import re
from .acl import EveryoneAclResolver, UnauthenticatedAclResolver, AuthenticatedAclResolver, OwnerAclResolver, AdminAclResolver





class PermissionResolver(object):
    RESOLVER_MAP = {
        '$everyone': EveryoneAclResolver,
        '$unauthenticated': UnauthenticatedAclResolver,
        '$authenticated': AuthenticatedAclResolver,
        '$owner': OwnerAclResolver,
        '$admin': AdminAclResolver
    }

    def __init__(self):
        from django.conf import settings
        from ..helpers import import_class

        for rName, cl in getattr(settings, 'DRFS_ACL_RESOLVERS', {}).items():
            self.RESOLVER_MAP[rName] = import_class(cl)


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
                    #if acl['principalId'] == '$unauthenticated' and permission == 'DENY':
                    #    raise exceptions.NotAuthenticated("DRFS: Not Authenticated")
                    if resolved == 'ALLOW':
                        break

        return resolved
