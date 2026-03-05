from rest_framework import mixins, viewsets
from rest_framework.response import Response

from grid.models import Grid
from package.models import Category, Package
from searchv3.models import SearchV3

from .mixins import MultiLookupFieldMixin
from .serializers import (
    CategorySerializer,
    GridSerializer,
    PackageSerializer,
    SearchV3Serializer,
)


class SearchV3ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Accepts a 'q' GET parameter.

    Returns SearchV3 (PostgreSQL FTS) results.
    """

    serializer_class = SearchV3Serializer

    def get_queryset(self):
        return SearchV3.objects.none()

    def list(self, request):
        qr = request.GET.get("q", "")
        queryset = SearchV3.objects.search(qr)[:20]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PackageViewSet(MultiLookupFieldMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows packages to be viewed or edited.
    """

    queryset = Package.objects.all().order_by("-id")
    serializer_class = PackageSerializer
    paginate_by = 20


class GridViewSet(MultiLookupFieldMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Grid.objects.all().prefetch_related("packages").order_by("-id")
    serializer_class = GridSerializer
    paginate_by = 20


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("-id")
    serializer_class = CategorySerializer
    paginate_by = 20
