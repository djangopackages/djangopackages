from django.contrib import admin

from package.models import Category, Package, PackageExample

class PackageExampleInline(admin.TabularInline):
    model = PackageExample
    
class PackageAdmin(admin.ModelAdmin):
    inlines = [
        PackageExampleInline,
    ]

admin.site.register(Category)
admin.site.register(Package, PackageAdmin)
#admin.site.register(PackageExample)