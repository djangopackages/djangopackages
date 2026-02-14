from django.contrib import admin
from reversion.admin import VersionAdmin

from grid.models import Element, Feature, Grid, GridPackage


class GridPackageInline(admin.TabularInline):
    model = GridPackage
    raw_id_fields = ["package"]


@admin.register(Grid)
class GridAdmin(VersionAdmin):
    inlines = [
        GridPackageInline,
    ]
    list_display = ["title", "header", "is_locked", "created"]
    list_display_links = ["title"]
    list_editable = ["header"]
    list_filter = ["header", "is_locked"]
    raw_id_fields = ["packages"]
    search_fields = ["title", "slug"]


@admin.register(Element)
class ElementAdmin(VersionAdmin):
    raw_id_fields = ["grid_package", "feature"]
    search_fields = [
        "grid_package__grid__title",
        "grid_package__package__title",
        "feature__title",
    ]


@admin.register(Feature)
class FeatureAdmin(VersionAdmin):
    raw_id_fields = ["grid"]
    search_fields = ["grid__title", "title"]


@admin.register(GridPackage)
class GridPackageAdmin(VersionAdmin):
    raw_id_fields = ["grid", "package"]
    search_fields = ["grid__title", "package__title"]
