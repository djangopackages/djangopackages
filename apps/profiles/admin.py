from django.contrib import admin

from reversion.admin import VersionAdmin

from profiles.models import Profile

admin.site.register(Profile, VersionAdmin)