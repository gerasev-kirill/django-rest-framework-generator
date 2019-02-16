# -*- coding: utf-8 -*-
import re
from .acl import EveryoneAclResolver, UnauthenticatedAclResolver, AuthenticatedAclResolver, OwnerAclResolver, AdminAclResolver


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
            if not isinstance(acl['property'], (list, tuple)):
                properties = [acl['property']]
            else:
                properties = acl['property']
            for p in properties:
                if is_func_name(p, property_func):
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
            if resolved == 'ALLOW':
                break
        return resolved
