import json
from collections.abc import Mapping
from collections import OrderedDict
from rest_framework import serializers
from rest_framework.authtoken import serializers as authtoken_serializers
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings as rest_api_settings
from rest_framework.fields import get_error_detail, set_value
from rest_framework.fields import SkipField


from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
try:
    # DEPRECATED
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    # django >= 4.0.0
    from django.utils.translation import gettext_lazy as _

try:
    from drf_loopback_js_filters.serializers import LoopbackJsSerializerMixin
except ImportError:
    class LoopbackJsSerializerMixin(object):
        pass




class UserLoginUsernameSerializer(authtoken_serializers.AuthTokenSerializer):
    pass


class UserLoginEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg)

        attrs['user'] = user
        return attrs




class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"))
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})

    def __init__(self, *args, **kwargs):
        super(UserRegisterSerializer, self).__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        self.ModelClass = get_user_model()

    def is_username_unique(self, username):
        return True

    def is_email_unique(self, email):
        return True

    def validate(self, attrs):
        fields = self.get_fields()

        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        _err_must_include = []
        if not username and fields['username'].required:
            _err_must_include.append('"username"')
        if not email and fields['email'].required:
            _err_must_include.append('"username"')
        if not password and fields['password'].required:
            _err_must_include.append('"password"')

        if _err_must_include:
            msg = _('Must include '+ ' and '.join(_err_must_include) +'.')
            raise serializers.ValidationError(msg)

        if not self.is_email_unique(email):
            msg = _('"email" field should be unique.')
            raise serializers.ValidationError(msg)

        if not self.is_username_unique(username):
            msg = _('"username" field should be unique.')
            raise serializers.ValidationError(msg)

        return {
            'username': username,
            'email': email,
            'password': password
        }

    def create(self, validated_data):
        try:
            instance = self.ModelClass.objects.create_user(**validated_data)
            instance.save()
        except TypeError as exc:
            msg = (
                'Got a `TypeError` when calling `%s.objects.create_user()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.objects.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception text was: %s.' %
                (
                    self.ModelClass.__name__,
                    self.ModelClass.__name__,
                    self.__class__.__name__,
                    exc
                )
            )
            raise TypeError(msg)

        return instance


class UserRegisterUsernameUniqueSerializer(UserRegisterSerializer):

    def is_username_unique(self, username):
        try:
            self.ModelClass.objects.get(username=username)
            return False
        except:
            return True


class UserRegisterEmailUniqueSerializer(UserRegisterSerializer):

    def is_email_unique(self, email):
        try:
            self.ModelClass.objects.get(email=email)
            return False
        except:
            return True



class UserRegisterUsernameAndEmailUniqueSerializer(UserRegisterSerializer):

    def is_username_unique(self, username):
        try:
            self.ModelClass.objects.get(username=username)
            return False
        except:
            return True

    def is_email_unique(self, email):
        try:
            self.ModelClass.objects.get(email=email)
            return False
        except:
            return True



class UserLoggedInfoSerializer(serializers.Serializer):
    token = serializers.CharField(label=_("Auth token"))
    userId = serializers.IntegerField(label=_("User id"))
    user = serializers.JSONField(label=_("User data"))



class BaseModelSerializer(LoopbackJsSerializerMixin):
    def __init__(self, *args, **kwargs):
        super(BaseModelSerializer, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        """
        копия https://github.com/encode/django-rest-framework/blob/master/rest_framework/serializers.py
        нужна, чтоб игнорить загрузку строк как файлов
        """
        if not isinstance(data, Mapping):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise ValidationError({
                rest_api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='invalid')

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            if isinstance(field, (serializers.FileField, serializers.ImageField)):
                # поймали файловое поле
                if isinstance(primitive_value, str) and primitive_value:
                    continue
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret


    def get_fields(self, *args, **kwargs):
        fields = super(BaseModelSerializer, self).get_fields(*args, **kwargs)
        if not hasattr(self, '_context'):
            return fields
        request = self._context.get('request', {})
        if not hasattr(request, 'query_params') or not request.query_params.get('expand', None):
            return fields

        def raise_exception(detail):
            if getattr(self.Meta, 'raise_expand_exception', False):
                raise ValidationError(detail)


        try:
            expansion = json.loads(request.query_params.get('expand'))
        except:
            raise_exception("Query param 'expand' is invalid JSON")
            return fields
        if not isinstance(expansion, dict):
            raise_exception("Query param 'expand' is invalid. Allowed dict only")
            return fields

        expand_fields = []
        expandable_fields = getattr(self.Meta, 'expandable_fields', None) or {}
        for field in expansion or {}:
            if not expansion[field] or field not in expandable_fields:
                raise_exception("Expand: field '{name}' is not expandable".format(name=field))
                continue
            expand_fields.append(field)

        if not expand_fields:
            return fields

        from drfs import generate_serializer

        for field in expand_fields:
            if field not in fields:
                continue
            has_queryset = False
            has_many = False
            if hasattr(fields[field], 'child_relation') and hasattr(fields[field].child_relation, 'queryset'):
                queryset = fields[field].child_relation.queryset
                has_queryset = True
                has_many = True
            if hasattr(fields[field], 'queryset'):
                queryset = fields[field].queryset
                has_queryset = True
            if not has_queryset:
                continue
            serializer_class = generate_serializer(
                queryset.model,
                visible_fields=self.Meta.expandable_fields[field].get('visible_fields', []),
                hidden_fields=[]
            )
            if self.Meta.expandable_fields[field].get('read_only', False):
                serializer_class.Meta.read_only_fields = self.Meta.expandable_fields[field].get('visible_fields', [])
            fields['$'+field] = serializer_class(many=has_many, source=field)
        return fields
