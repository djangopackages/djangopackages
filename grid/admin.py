from django.contrib import admin
from reversion.admin import VersionAdmin

from grid.models import Element, Feature, Grid, GridPackage


class GridPackageInline(admin.TabularInline):
    model = GridPackage


class GridAdmin(VersionAdmin):
    list_display_links = ('title',)
    list_display = ('title', 'header',)
    list_editable = ('header',)
    raw_id_fields = ["packages"]
    search_fields = ("title", "slug", "packages",)
    inlines = [
        GridPackageInline,
    ]

class ElementAdmin(VersionAdmin):
    raw_id_fields = ["grid_package", "feature"]
    search_fields = ("grid_package", "feature",)

class FeatureAdmin(VersionAdmin):
    raw_id_fields = ["grid"]
    search_fields = ("grid", "title",)

class GridPackageAdmin(VersionAdmin):
    raw_id_fields = ["grid"]
    search_fields = ("grid", "package",)

admin.site.register(Element, ElementAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(Grid, GridAdmin)
admin.site.register(GridPackage, GridPackageAdmin)
