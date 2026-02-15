from django.contrib import admin

from searchv3.models import SearchV3


@admin.register(SearchV3)
class SearchV3Admin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "weight",
        "item_type",
        "category",
        "pypi_downloads",
        "repo_watchers",
        "score",
    ]
    list_filter = ["item_type", "category"]
    ordering = ["-weight"]
    search_fields = ["title", "category"]
    readonly_fields = ["search_vector"]
