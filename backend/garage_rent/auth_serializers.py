from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from djoser.serializers import UserSerializer


class VerifiedUserSerializer(UserSerializer):
    email_verified = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = tuple(UserSerializer.Meta.fields) + ("email_verified",)

    def get_email_verified(self, obj):
        verification = getattr(obj, "email_verification", None)
        return bool(verification and verification.email.lower() == obj.email.lower())


class EmailUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = ("username", "email", "password")

    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("Informe um e-mail.")
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Este e-mail já está cadastrado.")
        return email


class EmailUserCreatePasswordRetypeSerializer(UserCreatePasswordRetypeSerializer, EmailUserCreateSerializer):
    class Meta(EmailUserCreateSerializer.Meta):
        pass


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username")
        self.fields["email"] = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.pop("email").strip()
        users = get_user_model().objects.filter(email__iexact=email)
        if users.count() != 1:
            raise AuthenticationFailed("E-mail ou senha inválidos.")
        attrs["username"] = users.get().get_username()
        return super().validate(attrs)
