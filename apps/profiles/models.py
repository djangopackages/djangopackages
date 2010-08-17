from django.db import models
from django.utils.translation import ugettext_lazy as _

from idios.models import ProfileBase


class Profile(ProfileBase):
    github_url = models.CharField(_("Github account"), null=True, blank=True, max_length=100)
    bitbucket_url = models.CharField(_("Bitbucket account"), null=True, blank=True, max_length=100)
    google_code_url = models.CharField(_("Google Code account"), null=True, blank=True, max_length=100)

    class Meta:
        permissions = (
            ("is_moderator", "is_moderator"),
        )