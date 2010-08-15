from django.contrib import admin

from package.models import Category, Package, PackageExample, Repo

class PackageExampleInline(admin.TabularInline):
    model = PackageExample
    
class PackageAdmin(admin.ModelAdmin):
    inlines = [
        PackageExampleInline,
    ]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'repo', 'repo_url', 'related_packages')
        }),
        ('Pulled data', {
            'classes': ('collapse',),
            'fields': ('repo_description', 'repo_watchers', 'repo_forks', 'pypi_version', 'pypi_downloads', 'participants')
        }),
    )    

admin.site.register(Category)
admin.site.register(Package, PackageAdmin)
admin.site.register(Repo)