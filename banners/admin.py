from django.contrib import admin

from banners.models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "banner_type", "start_date", "end_date", "created"]
    list_filter = ["banner_type"]
    search_fields = ["title", "content"]
    readonly_fields = ["created", "modified"]
    fieldsets = (
        (
            "Content",
            {
                "fields": ("title", "content", "banner_type"),
            },
        ),
        (
            "Scheduling",
            {
                "fields": ("start_date", "end_date"),
            },
        ),
        (
            "Appearance",
            {
                "fields": ("is_dismissible", "icon", "alignment"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created", "modified"),
                "classes": ("collapse",),
            },
        ),
    )
