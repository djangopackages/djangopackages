from django.contrib import admin

from blog.models import Post, PostImage


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "published_date"]
    list_filter = ["status"]


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ["__str__", "markdown", "created"]
    readonly_fields = ["markdown"]
