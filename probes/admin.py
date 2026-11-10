from django.contrib import admin, messages

from probes import stats as probe_stats
from django.utils import timezone
from django.utils.html import format_html

from package.importer import import_from_pypi
from package.models import Category
from probes.models import Candidate, Library, PackageProbe, ProbeSymbol


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    """Where a library gets toggled on for scanning."""

    list_display = ["pypi_name", "import_name", "scan", "source", "package"]
    list_editable = ["scan"]
    list_filter = ["scan", "source"]
    list_select_related = ["package"]
    search_fields = ["pypi_name", "import_name"]
    autocomplete_fields = ["package"]
    readonly_fields = ["created", "modified"]


@admin.register(ProbeSymbol)
class ProbeSymbolAdmin(admin.ModelAdmin):
    """Where a symbol gets marked deprecated or removed.

    The counts are rebuilt by build_probe_catalog and are read-only
    here, so an edit cannot be silently undone by the next rebuild.

    A removal version set here changes the stats page, so every save
    and delete starts the cached roll-ups over.
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        probe_stats.invalidate()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        probe_stats.invalidate()

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        probe_stats.invalidate()


@admin.register(PackageProbe)
class PackageProbeAdmin(admin.ModelAdmin):
    """Read-only: every field here is written by a scan."""

    list_display = [
        "package",
        "python_range",
        "django_range",
        "wagtail_range",
        "django_cms_range",
        "files_scanned",
        "scanned_at",
    ]
    list_filter = ["python_source", "django_source"]
    list_select_related = ["package"]
    search_fields = ["package__slug", "package__title"]

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """The review queue for PyPI projects discovery found.

    Rows are written by `pypi_discover`; the admin is where a person
    decides. Approve runs the importer and links the package. Hold and
    reject record who decided and when, and a rejected name is never
    offered again.
    """

    list_display = [
        "name",
        "framework",
        "status",
        "version",
        "release_count",
        "first_release",
        "depends_on_django",
        "repo_link",
        "stars",
        "repo_created",
        "downloads",
        "dependents",
        "last_upload",
        "package",
    ]
    list_filter = ["status", "framework"]
    search_fields = ["name", "summary", "repo_url", "notes"]
    list_select_related = ["package", "reviewed_by"]
    autocomplete_fields = ["package"]
    date_hierarchy = "last_upload"
    actions = ["approve_and_import", "hold", "reject"]
    readonly_fields = [
        "name",
        "framework",
        "version",
        "summary",
        "home_page",
        "first_upload",
        "last_upload",
        "last_seen",
        "pypi_link",
        "pypi_fetched_at",
        "repo_url",
        "release_count",
        "first_release",
        "author",
        "requires_dist",
        "stars",
        "repo_created",
        "downloads",
        "dependents",
        "advisories",
        "ecosystems_fetched_at",
        "reviewed_by",
        "reviewed_at",
        "created",
        "modified",
    ]
    fieldsets = (
        (
            None,
            {"fields": ("name", "framework", "status", "reasons", "notes", "package")},
        ),
        (
            "From PyPI",
            {
                "fields": (
                    "pypi_link",
                    "version",
                    "summary",
                    "author",
                    "requires_dist",
                    "release_count",
                    "first_release",
                    "home_page",
                    "repo_url",
                    "first_upload",
                    "last_upload",
                    "pypi_fetched_at",
                )
            },
        ),
        (
            "From ecosyste.ms",
            {
                "fields": (
                    "stars",
                    "repo_created",
                    "downloads",
                    "dependents",
                    "advisories",
                    "ecosystems_fetched_at",
                )
            },
        ),
        (
            "Review",
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                    "last_seen",
                    "created",
                    "modified",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="PyPI")
    def pypi_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>', obj.pypi_url, obj.pypi_url
        )

    @admin.display(description="repository")
    def repo_link(self, obj):
        if not obj.repo_url:
            return ""
        short = obj.repo_url.removeprefix("https://").removeprefix("www.")
        return format_html('<a href="{}" target="_blank">{}</a>', obj.repo_url, short)

    @admin.display(description="releases")
    def release_count(self, obj):
        return obj.release_count or ""

    @admin.display(description="first release")
    def first_release(self, obj):
        return obj.first_release[:10]

    @admin.display(description="needs django", boolean=True)
    def depends_on_django(self, obj):
        return obj.depends_on_django

    @admin.display(description="author")
    def author(self, obj):
        return obj.author

    @admin.display(description="stars")
    def stars(self, obj):
        return obj.stars if obj.stars is not None else ""

    @admin.display(description="repo created")
    def repo_created(self, obj):
        return obj.repo_created

    @admin.display(description="downloads / mo")
    def downloads(self, obj):
        return obj.downloads if obj.downloads is not None else ""

    @admin.display(description="dependents")
    def dependents(self, obj):
        return obj.dependents if obj.dependents is not None else ""

    @admin.display(description="advisories")
    def advisories(self, obj):
        return obj.advisories

    @admin.display(description="requires_dist")
    def requires_dist(self, obj):
        return "\n".join(obj.requires_dist)

    def _decide(self, request, queryset, status):
        count = queryset.exclude(status=Candidate.Status.IMPORTED).update(
            status=status, reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} candidate(s) marked {status}.")

    @admin.action(description="Hold for review")
    def hold(self, request, queryset):
        self._decide(request, queryset, Candidate.Status.HELD)

    @admin.action(description="Reject")
    def reject(self, request, queryset):
        self._decide(request, queryset, Candidate.Status.REJECTED)

    @admin.action(description="Approve and import as packages")
    def approve_and_import(self, request, queryset):
        """Run the importer for each row. The importer marks the row
        imported and links the package; anything it could not create is
        reported and left approved so it shows up for another look."""
        category = Category.objects.get(slug=IMPORT_CATEGORY)
        now = timezone.now()
        created, skipped = 0, []
        for candidate in queryset.exclude(status=Candidate.Status.IMPORTED):
            candidate.status = Candidate.Status.APPROVED
            candidate.reviewed_by = request.user
            candidate.reviewed_at = now
            candidate.save(
                update_fields=["status", "reviewed_by", "reviewed_at", "modified"]
            )
            result = import_from_pypi(candidate.name, category=category)
            if result.created:
                created += 1
            elif result.status == "exists" and result.package:
                candidate.status = Candidate.Status.IMPORTED
                candidate.package = result.package
                candidate.save(update_fields=["status", "package", "modified"])
            else:
                skipped.append(
                    f"{candidate.name}: {result.status} {result.note}".strip()
                )
        self.message_user(request, f"{created} package(s) created.")
        for line in skipped:
            self.message_user(request, line, level=messages.WARNING)


# Imported packages land in the same category pypi_import defaults to.
IMPORT_CATEGORY = "apps"
