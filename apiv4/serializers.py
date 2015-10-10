from rest_framework import serializers

from grid.models import Grid
from package.models import Package, Category
from searchv2.models import SearchV2

class GridSerializer(serializers.ModelSerializer):
    packages = serializers.HyperlinkedRelatedField(many=True, view_name='apiv4:package-detail', read_only=True)

    class Meta:
        model = Grid

class PackageSerializer(serializers.HyperlinkedModelSerializer):
    # 'Source' is attached to the model attribute
    participants = serializers.ListField(source='participant_list')
    commits_over_52 = serializers.ListField(source='commits_over_52_listed')
    grids = serializers.HyperlinkedRelatedField(many=True, view_name='apiv4:grid-detail', read_only=True)
    category = serializers.HyperlinkedRelatedField(view_name='apiv4:category-detail', read_only=True)

    class Meta:
        model = Package
        fields = (
            'category',
            'grids',
            'id',
            'title',
            'slug',
            'last_updated',
            'last_fetched',
            'repo_url',
            'pypi_version',
            'created',
            'modified',
            'repo_forks',
            'repo_description',
            'pypi_url',
            'documentation_url',
            'repo_watchers',
            'commits_over_52',
            'participants',
        )


class SearchV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = SearchV2
        fields = (
            "weight",
            "item_type",
            "title",
            "title_no_prefix",
            "slug",
            "slug_no_prefix",
            "clean_title",
            "description",
            "category",
            "absolute_url",
            "repo_watchers",
            "repo_forks",
            "pypi_downloads",
            "usage",
            "last_committed",
            "last_released"
        )

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
