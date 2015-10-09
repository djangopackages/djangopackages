from rest_framework import mixins
from rest_framework import response
from rest_framework import routers
from rest_framework import viewsets

from package.models import Package
from searchv2.models import SearchV2
from searchv2.views import search_function

from .serializers import PackageSerializer, SearchV2Serializer


class SearchV2ViewSet(viewsets.ModelViewSet):
    serializer_class = SearchV2Serializer
    queryset = SearchV2.objects.all()

    def list(self, request):
        q = request.GET.get('q', '')
        return response.Response(search_function(q))


class PackageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows packages to be viewed or edited.
    """
    queryset = Package.objects.all().order_by('-id')
    serializer_class = PackageSerializer
    paginate_by = 20


router = routers.DefaultRouter()
router.register(r'packages', PackageViewSet)
router.register(r'search', SearchV2ViewSet)
