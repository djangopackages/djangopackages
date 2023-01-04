from django.contrib import admin

from products.models import Product, Release


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "active"]
    list_filter = ["active"]
    ordering = ["slug"]
    search_fields = ["title", "slug"]


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "cycle",
        "cycle_short_hand",
        "latest",
        "lts",
        "release",
        "eol",
    ]
    list_filter = ["lts", "discontinued", "product"]
    ordering = ["product__slug"]
    raw_id_fields = ["product"]
    search_fields = ["cycle", "cycle_short_hand", "latest"]
