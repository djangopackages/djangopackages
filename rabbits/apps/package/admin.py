from django.contrib import admin

from package.models import Package, PackageExample


admin.site.register(Package)
admin.site.register(PackageExample)