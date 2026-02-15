import emoji
from rest_framework import serializers

from grid.models import Grid
from package.models import Category, Package
from searchv2.models import SearchV2
from searchv3.models import SearchV3


class GridSerializer(serializers.ModelSerializer):
    packages = serializers.HyperlinkedRelatedField(
        many=True,
        view_name="apiv4:package-detail",
        read_only=True,
        lookup_url_kwarg="pk_or_slug",
    )

    class Meta:
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "is_locked",
            "packages",
            "header",
            "created",
            "modified",
        ]
        model = Grid


class PackageSerializer(serializers.HyperlinkedModelSerializer):
    # 'Source' is attached to the model attribute
    participants = serializers.ListField(source="participant_list")
    grids = serializers.HyperlinkedRelatedField(
        many=True,
        view_name="apiv4:grid-detail",
        read_only=True,
        lookup_url_kwarg="pk_or_slug",
    )
    category = serializers.HyperlinkedRelatedField(
        view_name="apiv4:category-detail", read_only=True
    )
    # These methods were removed from the model
    # So, we added them here as fields
    # to avoid changing API structure
    last_updated = serializers.DateTimeField(source="last_commit_date")
    pypi_version = serializers.CharField(source="latest_version_number")
    commits_over_52 = serializers.ListField(default=[], source="commits_over_52w")

    class Meta:
        model = Package
        fields = (
            "category",
            "grids",
            "id",
            "title",
            "slug",
            "last_updated",
            "last_fetched",
            "repo_url",
            "pypi_version",
            "created",
            "modified",
            "repo_forks",
            "repo_description",
            "pypi_url",
            "documentation_url",
            "repo_watchers",
            "commits_over_52",
            "participants",
        )


# TODO(searchv3): Remove this SearchV2 serializer after searchv3 is stable
# and searchv2 is fully retired.
class SearchV2Serializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = SearchV2
        exclude = [
            "id",
        ]

    def get_description(self, obj):
        return emoji.emojize(obj.description)

    def get_title(self, obj):
        return emoji.emojize(obj.title)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "title_plural",
            "show_pypi",
            "created",
            "modified",
        ]
        model = Category


class SearchV3Serializer(serializers.ModelSerializer):
    """Backward-compatible serializer for SearchV3 results."""

    description = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    # Compatibility fields (SearchV3 does not store these; return equivalents).
    title_no_prefix = serializers.SerializerMethodField()
    slug_no_prefix = serializers.SerializerMethodField()
    clean_title = serializers.SerializerMethodField()

    class Meta:
        model = SearchV3
        exclude = ["id", "search_vector"]

    def get_description(self, obj):
        return emoji.emojize(obj.description)

    def get_title(self, obj):
        return emoji.emojize(obj.title)

    def get_title_no_prefix(self, obj):
        return obj.title

    def get_slug_no_prefix(self, obj):
        return obj.slug

    def get_clean_title(self, obj):
        return obj.title
