from rest_framework import serializers
from rest_framework.authtoken import serializers as authtoken_serializers
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate



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
        from django.contrib.auth.models import User as ModelClass
        self.ModelClass = ModelClass

    def is_username_unique(self, username):
        return True

    def is_email_unique(self, email):
        return True

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        if not username or not email or not password:
            msg = _('Must include "username" and "email" and "password".')
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
            instance = self.ModelClass(**validated_data)
            instance.set_password(validated_data['password'])
            instance.save()
        except TypeError as exc:
            msg = (
                'Got a `TypeError` when calling `%s()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.objects.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception text was: %s.' %
                (
                    ModelClass.__name__,
                    ModelClass.__name__,
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
