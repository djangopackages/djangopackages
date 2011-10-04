from django.contrib import admin

from reversion.admin import VersionAdmin

from profiles.models import Profile

class ProfileAdmin(VersionAdmin):
    
    search_fields = ("user__username","github_account", "user__email", "email")
    list_display = ("github_account", "email", "email")

admin.site.register(Profile, ProfileAdmin)