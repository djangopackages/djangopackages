from rest_framework import serializers

from .models import Package


class PackageSerializer(serializers.ModelSerializer):
    pypi_version = serializers.CharField(max_length=50)
    usage_count = serializers.IntegerField()
    commits_over_52 = serializers.CharField(max_length=255)
    development_status = serializers.CharField(max_length=255)

    def transform_pypi_version(self, obj, value):
        return obj.pypi_version

    def transform_usage_count(self, obj, value):
        return obj.usage_count

    def transform_commits_over_52(self, obj, value):
        return obj.commits_over_52()

    def transform_development_status(self, obj, value):
        return obj.development_status

    class Meta:
        model = Package
        fields = (
                    "id",
                    "slug",
                    "title",
                    "repo_description",
                    "repo_watchers",
                    "repo_forks",
                    "pypi_version",
                    "usage_count",
                    "commits_over_52",
                    "development_status"
                )

