from django.contrib import admin

from pypi.models import PypiUpdateLog

class PypiUpdateLogAdmin(admin.ModelAdmin):
    
    list_display = ("modified", "last_update_success", )
    model = PypiUpdateLog

admin.site.register(PypiUpdateLog, PypiUpdateLogAdmin)