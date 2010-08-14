from django.contrib import admin

from package.models import Category, Package, PackageExample

admin.site.register(Category)
admin.site.register(Package)
admin.site.register(PackageExample)