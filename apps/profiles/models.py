from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from idios.models import ProfileBase

from package.models import Package
from package.models import Repo



class Profile(ProfileBase):
    github_url = models.CharField(_("Github account"), null=True, blank=True, max_length=100)
    bitbucket_url = models.CharField(_("Bitbucket account"), null=True, blank=True, max_length=100)
    google_code_url = models.CharField(_("Google Code account"), null=True, blank=True, max_length=100)

    class Meta:
        permissions = (
            ("is_moderator", "is_moderator"),
        )
        
    def my_packages(self):
        # Move these bits into the Repo model
        name = self.bitbucket_url
        bitbucket_regex = r'^%s,|,%s,|%s$' % (name, name, name)
        bitbucket_repo = Repo.objects.get(title = 'BitBucket')
        
        name = self.github_url
        github_regex = r'^%s,|,%s,|%s$' % (name, name, name)
        github_repo = Repo.objects.get(title = 'Github')

        
        return Package.objects.filter(
                (Q(participants__regex=bitbucket_regex) & Q(repo=bitbucket_repo)) |
                (Q(participants__regex=github_regex) & Q(repo=github_repo))                
        )
        
        