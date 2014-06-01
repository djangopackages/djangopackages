from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import BaseModel


class Profile(BaseModel):
    user = models.OneToOneField(User)

    # Note to coders: The '_url' fields below need to JUST be the name of the account.
    #     Examples:
    #       github_url = 'pydanny'
    #       bitbucket_url = 'pydanny'
    #       google_code_url = 'pydanny'
    github_account = models.CharField(_("Github account"), null=True, blank=True, max_length=40)
    github_url = models.CharField(_("Github account"), null=True, blank=True, max_length=100, editable=False)
    bitbucket_url = models.CharField(_("Bitbucket account"), null=True, blank=True, max_length=100)
    google_code_url = models.CharField(_("Google Code account"), null=True, blank=True, max_length=100)
    email = models.EmailField(_("Email"), null=True, blank=True)

    def __unicode__(self):
        if not self.github_account:
            return self.user.username
        return self.github_account

    def save(self, **kwargs):
        """ Override save to always populate email changes to auth.user model
        """
        if self.email is not None:

            email = self.email.strip()
            user_obj = User.objects.get(username=self.user.username)
            user_obj.email = email
            user_obj.save()

        super(Profile, self).save(**kwargs)

    def url_for_repo(self, repo):
        """Return the profile's URL for a given repo.

        If url doesn't exist return None.
        """
        url_mapping = {
            'Github': self.github_account,
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

    @models.permalink
    def get_absolute_url(self):
        return ("profile_detail", [self.github_account])

    # define permission properties as properties so we can access in templates

    @property
    def can_add_package(self):
        if getattr(settings, 'RESTRICT_PACKAGE_EDITORS', False):
            return self.user.has_perm('package.add_package')
        # anyone can add
        return True

    @property
    def can_edit_package(self):
        if getattr(settings, 'RESTRICT_PACKAGE_EDITORS', False):
            # this is inconsistent, fix later?
            return self.user.has_perm('package.change_package')
        # anyone can edit
        return True

    # Grids
    @property
    def can_edit_grid(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.change_grid')
        return True

    @property
    def can_add_grid(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.add_grid')
        return True

    # Grid Features
    @property
    def can_add_grid_feature(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.add_feature')
        return True

    @property
    def can_edit_grid_feature(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.change_feature')
        return True

    @property
    def can_delete_grid_feature(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.delete_feature')
        return True

    # Grid Packages
    @property
    def can_add_grid_package(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.add_gridpackage')
        return True

    @property
    def can_delete_grid_package(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.delete_gridpackage')
        return True

    # Grid Element (cells in grid)
    @property
    def can_edit_grid_element(self):
        if getattr(settings, 'RESTRICT_GRID_EDITORS', False):
            return self.user.has_perm('grid.change_element')
        return True