from django.contrib import admin
from reversion.admin import VersionAdmin

from package.models import Category, Package, PackageExample, Commit, Version


class PackageExampleInline(admin.TabularInline):
    model = PackageExample
    raw_id_fields = ["created_by"]


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ["__str__", "commit_date"]
    raw_id_fields = ["package"]


@admin.register(Package)
class PackageAdmin(VersionAdmin):
    save_on_top = True
    search_fields = ["title"]
    list_filter = ["category", "supports_python3"]
    list_display = ["title", "category", "score", "supports_python3", "created"]
    date_hierarchy = "created"
    raw_id_fields = ["usage", "deprecated_by", "deprecates_package"]
    inlines = [
        PackageExampleInline,
    ]
    readonly_fields = ["score", "created_by", "last_modified_by"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "pypi_url",
                    "repo_url",
                    "usage",
                    "score",
                    "created_by",
                    "last_modified_by",
                    "date_deprecated",
                    "deprecates_package",
                    "deprecated_by",
                )
            },
        ),
        (
            "Pulled data",
            {
                "classes": ("collapse",),
                "fields": (
                    "repo_description",
                    "repo_watchers",
                    "repo_forks",
                    "date_repo_archived",
                    "commit_list",
                    "pypi_downloads",
                    "pypi_classifiers",
                    "pypi_license",
                    "pypi_licenses",
                    "pypi_requires_python",
                    "supports_python3",
                    "participants",
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


@admin.register(Version)
class VersionLocalAdmin(admin.ModelAdmin):
    list_display = ["__str__", "license", "hidden", "supports_python3", "created"]
    list_filter = ["hidden", "supports_python3", "created", "development_status"]
    ordering = ["-created"]
    raw_id_fields = ["package"]
    search_fields = ["package__title"]


admin.site.register(Category, VersionAdmin)
