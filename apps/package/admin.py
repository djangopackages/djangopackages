from django.contrib import admin

from package.models import Category, Package, PackageExample, Repo

class PackageExampleInline(admin.TabularInline):
    model = PackageExample
    
class PackageAdmin(admin.ModelAdmin):
    
    search_fields = ('title',)
    list_filter = ('category','repo')    
    list_display = ('title', 'created', )
    date_hierarchy = 'created'    
    inlines = [
        PackageExampleInline,
    ]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'pypi_url', 'repo', 'repo_url', 'related_packages')
        }),
        ('Pulled data', {
            'classes': ('collapse',),
            'fields': ('repo_description', 'repo_watchers', 'repo_forks', 'repo_commits', 'pypi_version', 'pypi_downloads', 'participants')
        }),
    )    

admin.site.register(Category)
admin.site.register(Package, PackageAdmin)
admin.site.register(Repo)