from django.contrib import admin

from probes.models import Library, PackageProbe, ProbeSymbol


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    """Where a library gets toggled on for scanning."""

    list_display = ["pypi_name", "import_name", "scan", "source", "package"]
    list_editable = ["scan"]
    list_filter = ["scan", "source"]
    search_fields = ["pypi_name", "import_name"]
    autocomplete_fields = ["package"]
    readonly_fields = ["created", "modified"]


@admin.register(ProbeSymbol)
class ProbeSymbolAdmin(admin.ModelAdmin):
    """Where a symbol gets marked deprecated or removed.

    The counts are rebuilt by build_probe_catalog and are read-only
    here, so an edit cannot be silently undone by the next rebuild.
    """

    list_display = [
        "name",
        "library",
        "kind",
        "packages",
        "uses",
        "deprecated",
        "deprecated_in",
        "removed_in",
    ]
    list_editable = ["deprecated", "deprecated_in", "removed_in"]
    list_filter = ["kind", "library", "deprecated"]
    search_fields = ["name"]
    readonly_fields = [
        "packages",
        "uses",
        "counted_at",
        "created",
        "modified",
    ]


@admin.register(PackageProbe)
class PackageProbeAdmin(admin.ModelAdmin):
    """Read-only: every field here is written by a scan."""

    list_display = [
        "package",
        "python_range",
        "django_range",
        "files_scanned",
        "scanned_at",
    ]
    list_filter = ["python_source", "django_source"]
    search_fields = ["package__slug", "package__title"]
    autocomplete_fields = ["package"]

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]
