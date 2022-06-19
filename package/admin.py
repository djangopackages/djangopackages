from django.contrib import admin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from reversion.admin import VersionAdmin

from package.models import Category, FlaggedPackage, Package, PackageExample, Commit, Version


class PackageExampleInline(admin.TabularInline):
    model = PackageExample
    raw_id_fields = ["created_by"]


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ["__str__", "commit_date"]
    raw_id_fields = ["package"]


@admin.register(Package)
class PackageAdmin(VersionAdmin, DynamicArrayMixin):
    save_on_top = True
    search_fields = ["title", "slug"]
    list_filter = [
        "category",
        "supports_python3",
        "date_repo_archived",
        "date_deprecated",
    ]
    list_display = [
        "title",
        "score",
        "last_exception_count",
        "date_repo_archived",
        "date_deprecated",
        "last_fetched",
        "created",
    ]
    date_hierarchy = "created"
    raw_id_fields = ["usage", "deprecated_by", "deprecates_package"]
    inlines = [
        PackageExampleInline,
    ]
    readonly_fields = [
        "commit_list",
        "created_by",
        "last_exception",
        "last_exception_at",
        "last_exception_count",
        "last_modified_by",
        "participants",
        "repo_description",
        "repo_forks",
        "repo_watchers",
        "score",
        "supports_python3",
        "supports_python3",
        "usage",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "repo_url",
                    # "usage",
                    "score",
                    "date_repo_archived",
                    "markers",
                    "created_by",
                    "last_modified_by",
                )
            },
        ),
        (
            "Deprecation data",
            {
                "fields": (
                    "date_deprecated",
                    "deprecates_package",
                    "deprecated_by",
                ),
            },
        ),
        (
            "PyPi data",
            {
                "fields": (
                    "pypi_url",
                    "pypi_downloads",
                    "pypi_info",
                    "pypi_license",
                    "pypi_licenses",
                    "pypi_requires_python",
                    "pypi_classifiers",
                ),
            },
        ),
        (
            "Pulled data",
            {
                # "classes": ("collapse",),
                "fields": (
                    "repo_description",
                    "repo_watchers",
                    "repo_forks",
                    "commit_list",
                    "supports_python3",
                    "participants",
                ),
            },
        ),
        (
            "Exceptions",
            {
                "fields": (
                    "last_exception",
                    "last_exception_at",
                    "last_exception_count",
                ),
            },
        ),
    )


@admin.register(PackageExample)
class PackageExampleAdmin(admin.ModelAdmin):
    list_display = [
        "title",
    ]
    raw_id_fields = ["package"]
    readonly_fields = ["created_by"]
    search_fields = ["title"]

@admin.register(FlaggedPackage)
class FlaggedPackageAdmin(admin.ModelAdmin):
    list_display = [
        "package",
        "reason",
        "created",
    ]
    raw_id_fields = ["package"]
    search_fields = ["package__title"]

@admin.register(Version)
class VersionLocalAdmin(admin.ModelAdmin):
    list_display = ["__str__", "license", "hidden", "supports_python3", "created"]
    list_filter = ["hidden", "supports_python3", "created", "development_status"]
    ordering = ["-created"]
    raw_id_fields = ["package"]
    search_fields = ["package__title"]


admin.site.register(Category, VersionAdmin)
