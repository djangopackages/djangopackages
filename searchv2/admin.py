from django.contrib import admin

from searchv2.models import SearchV2


@admin.register(SearchV2)
class SearchV2Admin(admin.ModelAdmin):
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
    search_fields = ["title", "title_no_prefix", "category"]
