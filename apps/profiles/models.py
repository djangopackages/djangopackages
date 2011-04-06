from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from idios.models import ProfileBase

from package.models import Package



class Profile(ProfileBase):
    github_url = models.CharField(_("Github account"), null=True, blank=True, max_length=100)
    bitbucket_url = models.CharField(_("Bitbucket account"), null=True, blank=True, max_length=100)
    google_code_url = models.CharField(_("Google Code account"), null=True, blank=True, max_length=100)

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

