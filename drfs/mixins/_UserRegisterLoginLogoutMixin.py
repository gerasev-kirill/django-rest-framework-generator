from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

from drfs.decorators import action

from ..serializers import rest as serializers_rest





class UserRegisterLoginLogoutMixin(object):
    user_serializer_class = None
    user_register_serializer_class = serializers_rest.UserRegisterSerializer
    user_login_serializer_class = serializers_rest.UserLoginUsernameSerializer

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

    @action(methods=['post'], detail=False)
    def login(self, request, *args, **kwargs):
        """
        Login a user with username/email and password(depend on serializer)
        ---
        omit_serializer: true
        type:
            token:
              required: true
              type: string
            userId:
              required: true
              type: number
            user:
              type: object
        parameters:
            - name: username
              required: true
              type: string
              paramType: form
            - name: password
              required: true
              type: string
              paramType: form
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

    @action(methods=['delete'], detail=False)
    def logout(self, request, *args, **kwargs):
        """
        Logout a user with access token
        ---
        omit_serializer: true
        responseMessages:
            - code: 204
              message: Request was successful
        """
        tAuth = TokenAuthentication()
        user, token = tAuth.authenticate(request)
        self.perform_logout(user, token)
        return Response({}, status=204)



    def perform_reset_password(self, user, token):
        pass

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
