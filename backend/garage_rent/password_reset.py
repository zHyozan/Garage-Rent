from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["re_password"]:
            raise serializers.ValidationError({"re_password": "As senhas não coincidem."})
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = get_user_model().objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            raise serializers.ValidationError({"token": "Link inválido ou expirado."})
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Link inválido ou expirado."})
        try:
            validate_password(attrs["password"], user)
        except ValidationError as error:
            raise serializers.ValidationError({"password": error.messages})
        attrs["user"] = user
        return attrs


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = get_user_model().objects.filter(email__iexact=serializer.validated_data["email"], is_active=True)
        if users.count() == 1:
            user = users.get()
            uid = urlsafe_base64_encode(str(user.pk).encode())
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/redefinir-senha?uid={uid}&token={token}"
            send_mail(
                "Redefinir senha do Garage Rent",
                f"Para criar uma nova senha, acesse este link (válido por 1 hora):\n{link}\n\nSe você não solicitou a alteração, ignore esta mensagem.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
        return Response({"detail": "Se o e-mail estiver cadastrado, enviaremos um link de recuperação."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)
