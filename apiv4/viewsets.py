from rest_framework import mixins
from rest_framework.response import Response
from rest_framework import routers
from rest_framework import viewsets

from package.models import Package
from searchv2.models import SearchV2
from searchv2.views import search_function

from .serializers import PackageSerializer, SearchV2Serializer


class SearchV2ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SearchV2Serializer
    queryset = SearchV2.objects.all()

    def list(self, request):
        qr = request.GET.get('q', '')
        queryset = search_function(qr)[:10]
        serializer = SearchV2Serializer(queryset, many=True)
        return Response(serializer.data)


class PackageViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows packages to be viewed or edited.
    """
    queryset = Package.objects.all().order_by('-id')
    serializer_class = PackageSerializer
    paginate_by = 20


router = routers.DefaultRouter()
# router.register(r'packages', PackageViewSet)
router.register(r'search', SearchV2ViewSet)
