from rest_framework.routers import DefaultRouter
from .views import SpaceViewSet

router = DefaultRouter()
router.register("", SpaceViewSet, basename="space")

urlpatterns = router.urls
