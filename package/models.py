from datetime import datetime, timedelta
import re

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _

from distutils.version import LooseVersion as versioner

from core.utils import STATUS_CHOICES
from core.models import BaseModel
from package.pypi import fetch_releases
from package.repos import get_repo_for_repo_url
from package.signals import signal_fetch_latest_metadata
from package.utils import get_version, get_pypi_version

repo_url_help_text = settings.PACKAGINATOR_HELP_TEXT['REPO_URL']
pypi_url_help_text = settings.PACKAGINATOR_HELP_TEXT['PYPI_URL']


class NoPyPiVersionFound(Exception):
    pass


class Category(BaseModel):

    title = models.CharField(_("Title"), max_length="50")
    slug = models.SlugField(_("slug"))
    description = models.TextField(_("description"), blank=True)
    title_plural = models.CharField(_("Title Plural"), max_length="50", blank=True)
    show_pypi = models.BooleanField(_("Show pypi stats & version"), default=True)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return self.title


class Package(BaseModel):

    title = models.CharField(_("Title"), max_length="100")
    slug = models.SlugField(_("Slug"), help_text="Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.<br />Values will be converted to lowercase.", unique=True)
    category = models.ForeignKey(Category, verbose_name="Installation")
    repo_description = models.TextField(_("Repo Description"), blank=True)
    repo_url = models.URLField(_("repo URL"), help_text=repo_url_help_text, blank=True, unique=True, verify_exists=True)
    repo_watchers = models.IntegerField(_("repo watchers"), default=0)
    repo_forks = models.IntegerField(_("repo forks"), default=0)
    pypi_url = models.URLField(_("PyPI slug"), help_text=pypi_url_help_text, blank=True, default='', verify_exists=True)
    pypi_downloads = models.IntegerField(_("Pypi downloads"), default=0)
    participants = models.TextField(_("Participants"),
                        help_text="List of collaborats/participants on the project", blank=True)
    usage = models.ManyToManyField(User, blank=True)
    created_by = models.ForeignKey(User, blank=True, null=True, related_name="creator", on_delete=models.SET_NULL)
    last_modified_by = models.ForeignKey(User, blank=True, null=True, related_name="modifier", on_delete=models.SET_NULL)

    commit_list = models.TextField(_("Commit List"), blank=True)

    @property
    def pypi_name(self):
        """ return the pypi name of a package"""

        if not self.pypi_url.strip():
            return ""

        name = self.pypi_url.replace("http://pypi.python.org/pypi/", "")
        if "/" in name:
            return name[:name.index("/")]
        return name

    @property
    def last_updated(self):
        try:
            last_commit = self.commit_set.latest('commit_date')
            if last_commit:
                return last_commit.commit_date
        except ObjectDoesNotExist:
            pass

        return None

    @property
    def repo(self):
        return get_repo_for_repo_url(self.repo_url)

    @property
    def active_examples(self):
        return self.packageexample_set.filter(active=True)

    @property
    def license_latest(self):
        try:
            return self.version_set.latest().license
        except Version.DoesNotExist:
            return "UNKNOWN"

    def grids(self):

        return (x.grid for x in self.gridpackage_set.all())

    def repo_name(self):
        return re.sub(self.repo.url_regex, '', self.repo_url)

    def participant_list(self):

        return self.participants.split(',')

    def get_usage_count(self):
        return self.usage.count()

    def commits_over_52(self):
        if self.commit_list:
            result = self.commit_list
        else:
            result = str([0 for x in range(52)])
        return result.replace(" ", "").replace("[", "").replace("]", "")

    def fetch_metadata(self, *args, **kwargs):

        # Get the downloads from pypi
        if self.pypi_url.strip() and self.pypi_url != "http://pypi.python.org/pypi/":

            total_downloads = 0

            for release in fetch_releases(self.pypi_name):

                version, created = Version.objects.get_or_create(
                    package=self,
                    number=release.version
                )

                # add to total downloads
                total_downloads += release.downloads

                # add to versions
                version.downloads = release.downloads
                if hasattr(release, "upload_time"):
                    version.upload_time = release.upload_time
                version.license = release.license
                version.hidden = release._pypi_hidden
                version.development_status = release.development_status
                version.supports_python3 = release.supports_python3
                version.save()

            self.pypi_downloads = total_downloads

        self.repo.fetch_metadata(self)
        signal_fetch_latest_metadata.send(sender=self)
        self.save()

    def save(self, *args, **kwargs):
        if not self.repo_description:
            self.repo_description = ""
        super(Package, self).save(*args, **kwargs)

    def fetch_commits(self):
        self.repo.fetch_commits(self)

    def pypi_version(self):
        cache_name = self.cache_namer(self.pypi_version)
        version = cache.get(cache_name)
        if version is not None:
            return version
        version = get_pypi_version(self)
        cache.set(cache_name, version)
        return version

    def last_released(self):
        cache_name = self.cache_namer(self.last_released)
        version = cache.get(cache_name)
        if version is not None:
            return version
        version = get_version(self)
        cache.set(cache_name, version)
        return version

    @property
    def pypi_ancient(self):
        release = self.last_released()
        if release:
            return release.upload_time < datetime.now() - timedelta(365)
        return None

    @property
    def no_development(self):
        commit_date = self.last_updated
        if commit_date is not None:
            return commit_date < datetime.now() - timedelta(365)
        return None

    class Meta:
        ordering = ['title']
        get_latest_by = 'id'

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ("package", [self.slug])


class PackageExample(BaseModel):

    package = models.ForeignKey(Package)
    title = models.CharField(_("Title"), max_length="100")
    url = models.URLField(_("URL"))
    active = models.BooleanField(_("Active"), default=True, help_text="Moderators have to approve links before they are provided")

    class Meta:
        ordering = ['title']

    def __unicode__(self):
        return self.title


class Commit(BaseModel):

    package = models.ForeignKey(Package)
    commit_date = models.DateTimeField(_("Commit Date"))
    commit_hash = models.CharField(_("Commit Hash"), help_text="Example: Git sha or SVN commit id", max_length=150, blank=True, default="")

    class Meta:
        ordering = ['-commit_date']
        get_latest_by = 'commit_date'

    def __unicode__(self):
        return "Commit for '%s' on %s" % (self.package.title, unicode(self.commit_date))


class VersionManager(models.Manager):
    def by_version(self, *args, **kwargs):
        qs = self.get_query_set().filter(*args, **kwargs)
        return sorted(qs, key=lambda v: versioner(v.number))

    def by_version_not_hidden(self, *args, **kwargs):
        qs = self.get_query_set().filter(*args, **kwargs)
        qs = qs.filter(hidden=False)
        qs = sorted(qs, key=lambda v: versioner(v.number))
        qs.reverse()
        return qs


class Version(BaseModel):

    package = models.ForeignKey(Package, blank=True, null=True)
    number = models.CharField(_("Version"), max_length="100", default="", blank="")
    downloads = models.IntegerField(_("downloads"), default=0)
    license = models.CharField(_("license"), max_length="100")
    hidden = models.BooleanField(_("hidden"), default=False)
    upload_time = models.DateTimeField(_("upload_time"), help_text=_("When this was uploaded to PyPI"), blank=True, null=True)
    development_status = models.IntegerField(_("Development Status"), choices=STATUS_CHOICES, default=0)
    supports_python3 = models.BooleanField(_("Supports Python 3"), default=False)

    objects = VersionManager()

    class Meta:
        get_latest_by = 'upload_time'
        ordering = ['-upload_time']

    @property
    def pretty_license(self):
        return self.license.replace("License", "").replace("license", "")

    @property
    def pretty_status(self):
        return self.get_development_status_display().split(" ")[-1]

    def save(self, *args, **kwargs):
        if self.license is None:
            self.license = "UNKNOWN"
        elif self.license.strip() == "License :: OSI Approved :: Apache Software License":
            pass
        elif len(self.license.strip()) > 20:
            self.license = "Custom"

        # reset the latest_version cache on the package
        cache_name = self.package.cache_namer(self.package.last_released)
        cache.delete(cache_name)
        get_version(self.package)

        # reset the pypi_version cache on the package
        cache_name = self.package.cache_namer(self.package.pypi_version)
        cache.delete(cache_name)
        get_pypi_version(self.package)

        super(Version, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s: %s" % (self.package.title, self.number)
