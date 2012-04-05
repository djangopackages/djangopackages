from django.contrib import admin
from reversion.admin import VersionAdmin

from grid.models import Element, Feature, Grid, GridPackage


class GridPackageInline(admin.TabularInline):
    model = GridPackage


class GridAdmin(VersionAdmin):
    list_display_links = ('title',)
    list_display = ('title', 'header',)
    list_editable = ('header',)
    inlines = [
        GridPackageInline,
    ]

admin.site.register(Element, VersionAdmin)
admin.site.register(Feature, VersionAdmin)
admin.site.register(Grid, GridAdmin)
admin.site.register(GridPackage, VersionAdmin)
