# -*- coding: utf-8 -*-
import re
from .acl import EveryoneAclResolver, UnauthenticatedAclResolver, AuthenticatedAclResolver, OwnerAclResolver, AdminAclResolver, DjangoPermissionsAclResolver


regex_special_chars = ['(', ')', '.', '+', '^', '$', '*', '{', '}', '[', ']', '|', '?']

def is_regex(text):
    for ch in regex_special_chars:
        if ch in text:
            return True
    return False


def is_func_name(search_text, func_name):
    if is_regex(search_text):
        return re.match(search_text, func_name)
    # обычный текст
    return search_text == func_name




class PermissionResolver(object):
    RESOLVER_MAP = {
        '$everyone': EveryoneAclResolver,
        '$unauthenticated': UnauthenticatedAclResolver,
        '$authenticated': AuthenticatedAclResolver,
        '$owner': OwnerAclResolver,
        '$admin': AdminAclResolver,
        '$djangoPermissions': DjangoPermissionsAclResolver
    }

    def __init__(self):
        from django.conf import settings
        from ..helpers import import_class

        if hasattr(settings, 'DRFS_ACL_RESOLVERS'):
            raise ValueError('DRFS_ACL_RESOLVERS is not allowed anymore in settings. Use DRF_GENERATOR.acl_resolvers')
        for rName, cl in getattr(settings, 'DRF_GENERATOR', {}).get('acl_resolver', {}).items():
            self.RESOLVER_MAP[rName] = import_class(cl)


    def get_resolver_instance(self, name):
        r_cls = self.RESOLVER_MAP.get(name)
        return r_cls()


    def resolve_permission(self, request=None, view=None, func_name=None, func_params={}, obj=None, model_acl=[]):
        if not model_acl:
            return 'ALLOW'
        resolved = 'ALLOW'

        for acl in model_acl:
            properties = acl['property']
            if not isinstance(properties, (list, tuple)):
                properties = [properties]

            for p in properties:
                if not is_func_name(p, func_name):
                    continue
                r = self.get_resolver_instance(acl['principalId'])
                permission = r.get_permission(
                    request=request,
                    view=view,
                    func_name=func_name,
                    func_params=func_params,
                    obj=obj,
                    acl=acl
                )
                if permission:
                    resolved = acl['permission']
                    #if acl['principalId'] == '$unauthenticated' and permission == 'DENY':
                    #    raise exceptions.NotAuthenticated("DRFS: Not Authenticated")
                    if resolved == 'ALLOW':
                        break
            if resolved == 'ALLOW':
                break
        return resolved
