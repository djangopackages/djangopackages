from django.contrib import admin
from reversion.admin import VersionAdmin

from grid.models import Element, Feature, Grid, GridPackage


class GridPackageInline(admin.TabularInline):
    model = GridPackage
    raw_id_fields = ["package"]


@admin.register(Grid)
class GridAdmin(VersionAdmin):
    list_display_links = ('title',)
    list_display = ('title', 'header', "is_locked")
    list_editable = ('header',)
    list_filter = ('header', "is_locked")
    raw_id_fields = ["packages"]
    search_fields = ["title", "slug"]
    inlines = [
        GridPackageInline,
    ]


@admin.register(Element)
class ElementAdmin(VersionAdmin):
    raw_id_fields = ["grid_package", "feature"]
    search_fields = ["grid_package", "feature"]


@admin.register(Feature)
class FeatureAdmin(VersionAdmin):
    raw_id_fields = ["grid"]
    search_fields = ["grid", "title"]


@admin.register(GridPackage)
class GridPackageAdmin(VersionAdmin):
    raw_id_fields = ["grid", "package"]
    search_fields = ["grid", "package"]
