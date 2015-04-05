from django.contrib import admin

from reversion.admin import VersionAdmin

from profiles.models import Profile


def username(obj):
    return (obj.user.username)
username.short_description = "User username"


def user_email(obj):
    return (obj.user.email)
user_email.short_description = "User email"


class ProfileAdmin(VersionAdmin):

    search_fields = ("user__username", "github_account", "user__email", "email")
    list_display = ("github_account", "email", username, user_email)

admin.site.register(Profile, ProfileAdmin)
