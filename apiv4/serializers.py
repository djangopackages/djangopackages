from rest_framework import serializers

from package.models import Package
from searchv2.models import SearchV2


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = (
            'title',
            'slug',
            'last_updated',
            'repo_url',
            'pypi_version'
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
