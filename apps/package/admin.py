from django.contrib import admin
from reversion.admin import VersionAdmin

from package.models import Category, Package, PackageExample, Commit, Version

class PackageExampleInline(admin.TabularInline):
    model = PackageExample
    
class PackageAdmin(VersionAdmin):
    
    save_on_top = True    
    search_fields = ("title",)
    list_filter = ("category",)
    list_display = ("title", "created", )
    date_hierarchy = "created"    
    inlines = [
        PackageExampleInline,
    ]
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "category", "pypi_url", "repo_url", "usage", "created_by", "last_modified_by","pypi_home_page",)
        }),
        ("Pulled data", {
            "classes": ("collapse",),
            "fields": ("repo_description", "repo_watchers", "repo_forks", "repo_commits", "pypi_downloads", "participants")
        }),
    )    
    
class CommitAdmin(VersionAdmin):
    list_filter = ("package",)
    

admin.site.register(Category, VersionAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(Commit, CommitAdmin)
admin.site.register(Version, VersionAdmin)
