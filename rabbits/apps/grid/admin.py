from django.contrib import admin

from grid.models import Element, Feature, Grid, GridPackage

class GridPackageInline(admin.TabularInline):
    model = GridPackage
    
class GridAdmin(admin.ModelAdmin):
    inlines = [
        GridPackageInline,
    ]    

admin.site.register(Element)
admin.site.register(Feature)
admin.site.register(Grid, GridAdmin)
admin.site.register(GridPackage)
