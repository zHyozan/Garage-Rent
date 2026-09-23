from smtplib import SMTPException
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from spaces.models import EmailVerification

SALT = "garage-rent.email-verification"


class EmailVerificationRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_verification"

    def post(self, request):
        token = signing.dumps({"user": request.user.pk, "email": request.user.email}, salt=SALT)
        link = f"{settings.FRONTEND_URL}/verificar-email?token={token}"
        try:
            send_mail("Confirme seu e-mail no Garage Rent", f"Confirme seu e-mail pelo link (válido por 24 horas):\n{link}", settings.DEFAULT_FROM_EMAIL, [request.user.email])
        except (SMTPException, OSError):
            return Response({"detail": "Não foi possível enviar o e-mail. Tente novamente mais tarde."}, status=503)
        return Response({"detail": "Link de verificação enviado. Confira sua caixa de entrada."})


class EmailVerificationConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_verification"

    def post(self, request):
        token = request.data.get("token")
        if not isinstance(token, str):
            return Response({"detail": "Link inválido ou expirado."}, status=400)
        try:
            data = signing.loads(token, salt=SALT, max_age=86400)
            user = get_user_model().objects.get(pk=data["user"], email=data["email"], is_active=True)
        except (signing.BadSignature, KeyError, ValueError, get_user_model().DoesNotExist):
            return Response({"detail": "Link inválido ou expirado."}, status=400)
        EmailVerification.objects.update_or_create(user=user, defaults={"email": user.email, "verified_at": timezone.now()})
        return Response({"detail": "E-mail verificado com sucesso."})
