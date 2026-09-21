from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .auth_views import EmailTokenObtainPairView
from .password_reset import PasswordResetConfirmView, PasswordResetRequestView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/jwt/create/", EmailTokenObtainPairView.as_view(), name="jwt-create-email"),
    path("api/auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
    path("api/spaces/", include("spaces.urls")),
    path("api/reservations/", include("reservations.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
