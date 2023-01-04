from django.contrib import admin

from classifiers.models import Classifier


@admin.register(Classifier)
class ClassifiertAdmin(admin.ModelAdmin):
    list_display = ["classifier", "active", "created"]
    list_filter = ["active"]
    ordering = ["classifier"]
    search_fields = ["classifier"]
