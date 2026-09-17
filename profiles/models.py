from django.conf import settings
from django.contrib.auth.models import User
from datetime import timedelta
from functools import cached_property

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Note to coders: The '_url' fields below need to JUST be the name of the account.
    #     Examples:
    #       github_url = 'pydanny'
    #       bitbucket_url = 'pydanny'
    github_account = models.CharField(
        _("GitHub account"), null=True, blank=True, max_length=40
    )
    github_url = models.CharField(
        _("GitHub account"), null=True, blank=True, max_length=100, editable=False
    )
    bitbucket_url = models.CharField(
        _("Bitbucket account"), null=True, blank=True, max_length=100
    )
    gitlab_url = models.CharField(
        _("GitLab account"), null=True, blank=True, max_length=100
    )
    email = models.EmailField(_("Email"), null=True, blank=True)
    share_favorites = models.BooleanField(_("Share Favorites"), default=False)
    is_trusted_override = models.BooleanField(
        _("Trusted"),
        default=False,
        help_text=_("Skip the new-account review period for this user"),
    )

    def __str__(self):
        if not self.github_account:
            return self.user.username
        return self.github_account

    def save(self, **kwargs):
        """Override save to always populate email changes to auth.user model"""
        if self.email is not None:
            email = self.email.strip()
            user_obj = User.objects.get(username=self.user.username)
            user_obj.email = email
            user_obj.save()

        super().save(**kwargs)

    def url_for_repo(self, repo):
        """Return the profile's URL for a given repo.

        If url doesn't exist return None.
        """
        url_mapping = {
            "GitHub": self.github_account,
            "Bitbucket": self.bitbucket_url,
            "GitLab": self.gitlab_url,
        }
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
        packages.sort(key=lambda a: a.title)
        return packages

    def get_absolute_url(self):
        return reverse("profile_detail", args=[self.github_account])

    @cached_property
    def github_created_at(self):
        """When the linked GitHub account was created, if we've stored it."""
        social = self.user.social_auth.filter(provider="github").first()
        if social and (created_at := social.extra_data.get("created_at")):
            return parse_datetime(created_at)
        return None

    @cached_property
    def is_trusted(self):
        """Whether this account is past the new-account review period.

        Both the Django Packages account and the GitHub account must be old
        enough. Accounts with no stored GitHub creation date are judged on
        their Django Packages account alone.
        """
        if self.user.is_superuser or self.user.is_staff or self.is_trusted_override:
            return True

        now = timezone.now()
        if now - self.user.date_joined < timedelta(
            days=settings.NEW_ACCOUNT_REVIEW_DAYS
        ):
            return False

        github_created_at = self.github_created_at
        if github_created_at and now - github_created_at < timedelta(
            days=settings.NEW_GITHUB_ACCOUNT_REVIEW_DAYS
        ):
            return False

        return True

    def can_edit_pending_grid(self, grid):
        """New accounts may keep editing a grid they created until it's reviewed."""
        return not grid.is_approved and grid.created_by_id == self.user_id

    # define permission properties as properties so we can access in templates

    @property
    def can_add_package(self):
        if getattr(settings, "RESTRICT_PACKAGE_EDITORS", False):
            return self.user.has_perm("package.add_package")
        # anyone can add
        return True

    @property
    def can_edit_package(self):
        if getattr(settings, "RESTRICT_PACKAGE_EDITORS", False):
            # this is inconsistent, fix later?
            return self.user.has_perm("package.change_package")
        # anyone can edit
        return True

    # Grids
    @property
    def can_edit_grid(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.change_grid")
        return self.is_trusted

    @property
    def can_add_grid(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.add_grid")
        return True

    # Grid Features
    @property
    def can_add_grid_feature(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.add_feature")
        return self.is_trusted

    @property
    def can_edit_grid_feature(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.change_feature")
        return self.is_trusted

    @property
    def can_delete_grid_feature(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.delete_feature")
        return True

    # Grid Packages
    @property
    def can_add_grid_package(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.add_gridpackage")
        return self.is_trusted

    @property
    def can_delete_grid_package(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.delete_gridpackage")
        return True

    # Grid Element (cells in grid)
    @property
    def can_edit_grid_element(self):
        if getattr(settings, "RESTRICT_GRID_EDITORS", False):
            return self.user.has_perm("grid.change_element")
        return self.is_trusted

    def get_opengraph_image_url(self):
        return reverse("profile_opengraph", args=[self.github_account])


class ExtraField(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    label = models.CharField(max_length=256)
    url = models.URLField(max_length=256)

    def __str__(self):
        return f"{self.profile} - {self.url}"
