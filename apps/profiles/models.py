from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from idios.models import ProfileBase

from package.models import Package



class Profile(ProfileBase):
    github_url = models.CharField(_("Github account"), null=True, blank=True, max_length=100)
    bitbucket_url = models.CharField(_("Bitbucket account"), null=True, blank=True, max_length=100)
    google_code_url = models.CharField(_("Google Code account"), null=True, blank=True, max_length=100)

    class Meta:
        permissions = (
            ("is_moderator", "is_moderator"),
        )
        
    def url_for_repo(self, repo):
        """Return the profile's URL for a given repo.
        
        If url doesn't exist return None.
        """
        url_mapping = {
            'Github': self.github_url,
            'BitBucket': self.bitbucket_url,
            'Google Code': self.google_code_url}
        return url_mapping.get(repo.title)
        
    def my_packages(self):
        """Return a list of all packages the user contributes to.
        
        List is sorted by package name.
        """
        from package.repos import get_repo, supported_repos

        packages = []
        for repo in supported_repos():
            repo = get_repo(repo)
            repo_packages = repo.packages_for_profile(self)
            packages.extend(repo_packages)
        packages.sort(lambda a, b: cmp(a.title, b.title))
        return packages
