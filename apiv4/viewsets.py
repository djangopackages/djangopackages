from rest_framework import mixins, viewsets
from rest_framework.response import Response

from grid.models import Grid
from package.models import Category, Package
from searchv2.models import SearchV2
from searchv2.views import search_function

from .mixins import MultiLookupFieldMixin
from .serializers import (
    CategorySerializer,
    GridSerializer,
    PackageSerializer,
    SearchV2Serializer,
)


class SearchV2ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Accepts a 'q' GET parameter. Results are currently sorted only by
    their weight.
    """

    serializer_class = SearchV2Serializer
    queryset = SearchV2.objects.all()

    def list(self, request):
        qr = request.GET.get("q", "")
        queryset = search_function(qr)[:20]
        serializer = SearchV2Serializer(queryset, many=True)
        return Response(serializer.data)


class PackageViewSet(MultiLookupFieldMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows packages to be viewed or edited.
    """

    queryset = Package.objects.all().order_by("-id")
    serializer_class = PackageSerializer
    paginate_by = 20


class GridViewSet(MultiLookupFieldMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Grid.objects.all().order_by("-id")
    serializer_class = GridSerializer
    paginate_by = 20


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("-id")
    serializer_class = CategorySerializer
    paginate_by = 20
