from rest_framework import routers

from .viewsets import CategoryViewSet, GridViewSet, PackageViewSet, SearchV2ViewSet

app_name = "apiv4"

router = routers.DefaultRouter()
router.register(r"packages", PackageViewSet)
router.register(r"search", SearchV2ViewSet)
router.register(r"grids", GridViewSet)
router.register(r"categories", CategoryViewSet)

urlpatterns = router.urls
