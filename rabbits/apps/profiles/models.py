from django.db import models
from django.utils.translation import ugettext_lazy as _

from idios.models import ProfileBase


class Profile(ProfileBase):
    github_url = models.URLField(_("Github url"), help_text="i.e. http://github.com/[my-account]", null=True, blank=True, verify_exists=True)
    bitbucket_url = models.URLField(_("Bitbucket url"), help_text="i.e. http://bitbucket.com/[my-account]", null=True, blank=True, verify_exists=False)
    google_code_url = models.URLField(_("Google Code url"), help_text="i.e. http://code.google.com/u/[my-account]/", null=True, blank=True, verify_exists=False)

    class Meta:
        permissions = (
            ("is_moderator", "is_moderator"),
        )