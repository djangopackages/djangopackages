from django.contrib import admin
from reversion.admin import VersionAdmin

from profiles.models import Profile


@admin.display(description="User username")
def username(obj):
    return obj.user.username


@admin.display(description="User email")
def user_email(obj):
    return obj.user.email


@admin.register(Profile)
class ProfileAdmin(VersionAdmin):
    search_fields = ("user__username", "github_account", "user__email", "email")
    list_display = ("github_account", "email", username, user_email)
    autocomplete_fields = ['user']
