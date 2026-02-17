import waffle
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from grid.models import Grid
from package.models import Category, Package

# TODO(searchv3): Remove SearchV2 fallback imports after searchv3 is stable and
# the searchv2 app is fully removed.
from searchv2.models import SearchV2
from searchv2.views import search_function
from searchv3.models import SearchV3

from .mixins import MultiLookupFieldMixin
from .serializers import (
    CategorySerializer,
    GridSerializer,
    PackageSerializer,
    SearchV2Serializer,
    SearchV3Serializer,
)


class SearchV3ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Accepts a 'q' GET parameter.

    Delegates to SearchV3 (PostgreSQL FTS) or SearchV2 depending on the
    ``use_searchv3`` waffle flag.
    """

    def _use_searchv3(self):
        # TODO(searchv3): Remove waffle flag gate after searchv3 is stable and
        # searchv2 is retired.
        return waffle.flag_is_active(self.request, "use_searchv3")

    def get_serializer_class(self):
        if self._use_searchv3():
            return SearchV3Serializer
        return SearchV2Serializer

    def get_queryset(self):
        if self._use_searchv3():
            return SearchV3.objects.none()
        return SearchV2.objects.none()

    def list(self, request):
        qr = request.GET.get("q", "")
        if self._use_searchv3():
            queryset = SearchV3.objects.search(qr)[:20]
        else:
            queryset = search_function(qr)[:20]
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
