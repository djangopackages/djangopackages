from django.contrib import admin
from reversion.admin import VersionAdmin

from grid.models import Element, Feature, Grid, GridPackage


class GridPackageInline(admin.TabularInline):
    model = GridPackage
    raw_id_fields = ["package"]


@admin.register(Grid)
class GridAdmin(VersionAdmin):
    inlines = [
        GridPackageInline,
    ]
    actions = ["approve_grids"]
    list_display = [
        "title",
        "header",
        "is_locked",
        "is_approved",
        "created_by",
        "created",
    ]
    list_display_links = ["title"]
    list_editable = ["header"]
    list_filter = ["is_approved", "header", "is_locked"]
    list_select_related = ["created_by"]
    raw_id_fields = ["packages", "created_by"]
    search_fields = ["title", "slug"]

    @admin.action(description="Approve selected grids")
    def approve_grids(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Approved {updated} grid(s).")


@admin.register(Element)
class ElementAdmin(VersionAdmin):
    raw_id_fields = ["grid_package", "feature"]
    search_fields = [
        "grid_package__grid__title",
        "grid_package__package__title",
        "feature__title",
    ]


@admin.register(Feature)
class FeatureAdmin(VersionAdmin):
    raw_id_fields = ["grid"]
    search_fields = ["grid__title", "title"]


@admin.register(GridPackage)
class GridPackageAdmin(VersionAdmin):
    raw_id_fields = ["grid", "package"]
    search_fields = ["grid__title", "package__title"]
