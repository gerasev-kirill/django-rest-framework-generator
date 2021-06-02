from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from rest_framework.settings import api_settings as drf_api_settings

from drfs.decorators import action, drf_ignore_filter_backend, drf_api_doc

from ..serializers import rest as rest_serializers
from ..serializers import schema as schema_serializers


if not getattr(drf_api_settings, 'DEFAULT_SCHEMA_CLASS', None):
    # old drf
    try:
        from rest_framework.schemas.coreapi import AutoSchema as BaseAutoSchema
    except ImportError:
        BaseAutoSchema = object
else:
    BaseAutoSchema = drf_api_settings.DEFAULT_SCHEMA_CLASS


class UserSchema(BaseAutoSchema):
    def get_request_serializer(self, path, method):
        action = getattr(self.view, 'action', None)
        if action == 'login':
            return self.view.get_user_login_serializer_class()()
        if action == 'register':
            return self.view.get_user_register_serializer_class()()
        return super(UserSchema, self).get_request_serializer(path, method)

    def get_response_serializer(self, path, method):
        action = getattr(self.view, 'action', None)
        if action == 'login':
            return rest_serializers.UserLoggedInfoSerializer()
        return super(UserSchema, self).get_response_serializer(path, method)



class UserRegisterLoginLogoutMixin(object):
    user_serializer_class = None
    user_register_serializer_class = rest_serializers.UserRegisterSerializer
    user_login_serializer_class = rest_serializers.UserLoginUsernameSerializer
    schema = UserSchema()

    def get_user_serializer_class(self):
        assert self.user_serializer_class is not None, (
            "'%s' should either include a `user_serializer_class` attribute, "
            "or override the `get_user_serializer_class()` method."
            % self.__class__.__name__
        )
        return self.user_serializer_class

    def get_user_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for get_auth_data function
        """
        serializer_class = self.get_user_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_user_register_serializer_class(self):
        assert self.user_register_serializer_class is not None, (
            "'%s' should either include a `user_register_serializer_class` attribute, "
            "or override the `get_user_register_serializer_class()` method."
            % self.__class__.__name__
        )
        return self.user_register_serializer_class

    def get_user_register_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for user registration
        """
        serializer_class = self.get_user_register_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_user_login_serializer_class(self):
        assert self.user_login_serializer_class is not None, (
            "'%s' should either include a `user_login_serializer_class` attribute, "
            "or override the `get_user_login_serializer_class()` method."
            % self.__class__.__name__
        )
        return self.user_login_serializer_class

    def get_user_login_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for user registration
        """
        serializer_class = self.get_user_login_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


    #
    #


    def get_auth_data(self, request, user=None):
        if not user:
            return {}
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        serializer = self.get_user_serializer(user)
        return {
            'token': token.key,
            'userId': user.id,
            'user': serializer.data
        }



    def perform_register(self, serializer):
        serializer.save()

    @drf_ignore_filter_backend()
    @action(methods=['post'], detail=False)
    def register(self, request, *args, **kwargs):
        serializer = self.get_user_register_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_register(serializer)
        user = serializer.instance
        return Response(
            self.get_auth_data(request, user),
            status=201
        )



    def perform_login(self, serializer):
        pass

    @drf_ignore_filter_backend()
    @action(methods=['post'], detail=False)
    def login(self, request, *args, **kwargs):
        """
        Login a user with username/email and password(depend on serializer)
        """
        serializer = self.get_user_login_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_login(serializer)
        user = serializer.validated_data['user']
        return Response(
            self.get_auth_data(request, user)
        )



    def perform_logout(self, user, token):
        token.delete()

    @drf_ignore_filter_backend()
    @drf_api_doc(response_serializer=schema_serializers.EmptyJsonSerializer)
    @action(methods=['delete'], detail=False)
    def logout(self, request, *args, **kwargs):
        """
        Logout a user with access token
        """
        result = TokenAuthentication().authenticate(request)
        if not result or len(result) != 2:
            return Response({}, status=204)
        user, token = result
        self.perform_logout(user, token)
        return Response({}, status=204)



    def perform_reset_password(self, user, token):
        pass

    @drf_ignore_filter_backend()
    @drf_api_doc(response_serializer=schema_serializers.EmptyJsonSerializer)
    @action(methods=['post'], detail=False)
    def reset(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        if not email:
            raise exceptions.NotAcceptable("Field 'email' required")
        try:
            user = self.queryset.get(email=email)
        except:
            raise exceptions.NotAcceptable("Email not found")
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        self.perform_reset_password(user, token)
        return Response({}, status=204)



    def perform_set_password(self, user, new_password):
        user.set_password(new_password)
        user.save()

    @drf_ignore_filter_backend()
    @drf_api_doc(response_serializer=schema_serializers.EmptyJsonSerializer)
    @action(methods=['post'], detail=False)
    def set_password(self, request, *args, **kwargs):
        password = request.data.get('password', None)
        if not password:
            raise exceptions.NotAcceptable("New password field 'password' required")

        tAuth = TokenAuthentication()
        try:
            user, token = tAuth.authenticate(request)
        except:
            raise exceptions.NotAcceptable(detail="Unknown user or auth token")
        self.perform_set_password(user, password)
        return Response({})
