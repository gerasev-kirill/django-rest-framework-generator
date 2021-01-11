import six



class AclResolver(object):
    def get_permission(self, request=None, **kwargs):
        raise NotADirectoryError


class EveryoneAclResolver(AclResolver):
    def get_permission(self, request=None, **kwargs):
        return True


class UnauthenticatedAclResolver(AclResolver):
    def get_permission(self, request=None, **kwargs):
        return not request.user.is_authenticated


class AuthenticatedAclResolver(AclResolver):
    def get_permission(self, request=None,**kwargs):
        return request.user.is_authenticated


class OwnerAclResolver(AclResolver):
    def get_permission(self, request=None, obj=None, **kwargs):
        if not request.user.is_authenticated:
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



class DjangoPermissionsAclResolver(AclResolver):
    perms_map = {
        'list': ['{app_label}.view_{model_name}'],
        'retrieve': ['{app_label}.view_{model_name}'],
        'create': ['{app_label}.add_{model_name}'],
        'update': ['{app_label}.change_{model_name}'],
        'destroy': ['{app_label}.delete_{model_name}'],
    }

    def get_required_permissions(self, model_cls, func_name, method, special_perm):
        """
        Given a model and an method name, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name,
            'func_name': func_name,
            'method': method.lower()
        }
        permissions = [perm.format(**kwargs) for perm in self.perms_map.get(func_name, [])]
        if not permissions and special_perm:
            if not isinstance(special_perm, list):
                special_perm = [special_perm]
            permissions = [perm.format(**kwargs) for perm in special_perm]
        if not permissions:
            permissions.append("{app_label}.{method}_{model_name}_{func_name}".format(**kwargs))
        return permissions


    def get_permission(self, request=None, view=None, func_name=None, obj=None, acl={}, **kwargs):
        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
        else:
            queryset = getattr(view, 'queryset', None)
        if queryset is None:
            return False
        perms = self.get_required_permissions(
            queryset.model,
            func_name,
            request.method,
            acl.get('requiredCodename', [])
        )
        if not perms:
            return False
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_perms(perms)
        )



class AdminAclResolver(AclResolver):
    def get_permission(self, request=None, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_superuser
