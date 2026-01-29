from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User

# from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField
from looseversion import LooseVersion

from core.models import BaseModel
from core.utils import PackageStatus
from package.managers import PackageManager
from package.repos import get_repo_for_repo_url
from package.utils import get_pypi_version, get_version, normalize_license

repo_url_help_text = settings.PACKAGINATOR_HELP_TEXT["REPO_URL"]
pypi_url_help_text = settings.PACKAGINATOR_HELP_TEXT["PYPI_URL"]


class RepoHost(models.TextChoices):
    AUTO_DETECT = "", _("Auto-detect")
    BITBUCKET = "bitbucket", _("Bitbucket")
    GITHUB = "github", _("GitHub")
    GITLAB = "gitlab", _("GitLab")
    CODEBERG = "codeberg", _("Codeberg")
    FORGEJO = "forgejo", _("Forgejo")

    @classmethod
    def from_url(cls, url: str):
        url = url.lower()
        if "github.com" in url:
            return cls.GITHUB
        elif "gitlab.com" in url:
            return cls.GITLAB
        elif "bitbucket.org" in url:
            return cls.BITBUCKET
        elif "codeberg.org" in url:
            return cls.CODEBERG
        return cls.AUTO_DETECT


class NoPyPiVersionFound(Exception):
    pass


class Category(BaseModel):
    title = models.CharField(_("Title"), max_length=50)
    slug = models.SlugField(_("slug"))
    description = models.TextField(_("description"), blank=True)
    title_plural = models.CharField(_("Title Plural"), max_length=50, blank=True)
    show_pypi = models.BooleanField(_("Show pypi stats & version"), default=True)

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("category", args=[self.slug])


class Package(BaseModel):
    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(
        _("Slug"),
        help_text="Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens. Values will be converted to lowercase.",
        unique=True,
    )
    category = models.ForeignKey(
        Category, verbose_name="Installation", on_delete=models.PROTECT
    )
    repo_description = models.TextField(
        _("Repo Description"), blank=True, max_length=500
    )
    repo_url = models.URLField(
        _("repo URL"), help_text=repo_url_help_text, blank=True, unique=True
    )
    repo_host = models.CharField(
        _("Repo host"),
        max_length=30,
        choices=RepoHost,
        blank=True,
        default=RepoHost.AUTO_DETECT,
        help_text=_(
            "Select the hosting service when auto-detection cannot determine it."
        ),
    )
    repo_watchers = models.IntegerField(_("Stars"), default=0)
    repo_forks = models.IntegerField(_("repo forks"), default=0)
    pypi_url = models.CharField(
        _("PyPI slug"),
        max_length=255,
        help_text=pypi_url_help_text,
        blank=True,
        default="",
    )
    pypi_downloads = models.IntegerField(_("PyPI downloads"), default=0)
    pypi_classifiers = ArrayField(
        models.CharField(max_length=100), blank=True, null=True
    )
    pypi_info = models.JSONField(blank=True, null=True)
    pypi_license = models.CharField(
        _("PyPI License"), max_length=100, blank=True, null=True
    )
    pypi_licenses = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    pypi_requires_python = models.CharField(
        _("PyPI Requires Python"), max_length=100, blank=True, null=True
    )
    markers = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    supports_python3 = models.BooleanField(
        _("Supports Python 3"), blank=True, null=True
    )
    participants = models.TextField(
        _("Participants"),
        help_text="List of collaborats/participants on the project",
        blank=True,
    )
    favorite_count = models.IntegerField(
        _("Favorite"), default=0, help_text="Favorite count"
    )
    usage = models.ManyToManyField(User, blank=True)
    created_by = models.ForeignKey(
        User, blank=True, null=True, related_name="creator", on_delete=models.SET_NULL
    )
    last_modified_by = models.ForeignKey(
        User, blank=True, null=True, related_name="modifier", on_delete=models.SET_NULL
    )
    last_fetched = models.DateTimeField(blank=True, null=True, default=now)
    documentation_url = models.URLField(
        _("Documentation URL"), blank=True, null=True, default=""
    )

    commit_list = models.TextField(_("Commit List"), blank=True)
    score = models.IntegerField(_("Score"), default=0)

    date_deprecated = models.DateTimeField(blank=True, null=True)
    date_repo_archived = models.DateTimeField(
        _("date when repo was archived"), blank=True, null=True
    )
    deprecated_by = models.ForeignKey(
        User, blank=True, null=True, related_name="deprecator", on_delete=models.PROTECT
    )
    deprecates_package = models.ForeignKey(
        "self",
        blank=True,
        help_text="The Package that replaces *this* Package",
        null=True,
        on_delete=models.PROTECT,
        related_name="replacement",
    )
    last_exception = models.TextField(blank=True, null=True)
    last_exception_at = models.DateTimeField(blank=True, null=True)
    last_exception_count = models.IntegerField(default=0, blank=True, null=True)
    commit_count = models.IntegerField(_("Commit Count"), default=0)

    commits_over_52w = models.JSONField(_("Commit List Over 52 Weeks"), default=list)
    last_commit_date = models.DateTimeField(blank=True, null=True)
    latest_version = models.ForeignKey(
        "Version",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="latest_version_package",
    )

    objects = PackageManager()

    class Meta:
        ordering = ["title"]
        get_latest_by = "id"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("package", args=[self.slug])

    def get_opengraph_image_url(self):
        return reverse("package_opengraph", args=[self.slug])

    @property
    def is_deprecated(self):
        return self.date_deprecated is not None

    @property
    def has_favorite(self):
        if self.favorite_count > 0:
            return True
        return False

    def get_pypi_uri(self):
        if self.pypi_name and len(self.pypi_name):
            return f"https://pypi.org/project/{self.pypi_name}/"
        return None

    def get_pypi_json_uri(self):
        if self.pypi_name and len(self.pypi_name):
            return f"https://pypi.org/pypi/{self.pypi_name}/json"
        return None

    @property
    def pypi_name(self):
        """return the pypi name of a package"""

        if not self.pypi_url.strip():
            return ""

        name = self.pypi_url

        if "http://pypi.python.org/pypi/" in name:
            name = name.replace("http://pypi.python.org/pypi/", "")

        if "https://pypi.python.org/pypi/" in name:
            name = name.replace("https://pypi.python.org/pypi/", "")

        if "https://pypi.org/project/" in name:
            name = name.replace("https://pypi.org/project/", "")

        name = name.strip("/")

        return name

    def last_updated(self):
        cache_name = self.cache_namer(self.last_updated)
        last_commit = cache.get(cache_name)
        if last_commit is not None:
            return last_commit

        if self.last_commit_date:
            return self.last_commit_date

        try:
            last_commit = self.commit_set.latest("commit_date").commit_date
            if last_commit:
                cache.set(cache_name, last_commit)
                return last_commit
        except ObjectDoesNotExist:
            last_commit = None

        return last_commit

    @property
    def repo(self):
        return get_repo_for_repo_url(self.repo_url, self.repo_host or None)

    @property
    def active_examples(self):
        return self.packageexample_set.filter(active=True)

    @property
    def license_latest(self):
        prefetched_versions = None
        if hasattr(self, "_prefetched_versions"):
            prefetched_versions = getattr(self, "_prefetched_versions")

        # If versions were prefetched (even if empty), use them and do not hit
        # the DB.
        if prefetched_versions is not None:
            if not prefetched_versions:
                return "UNKNOWN"
            # Version model orders by -upload_time, so the first non-null upload_time
            # is the effective "latest".
            for v in prefetched_versions:
                if v.upload_time is not None:
                    return v.license or "UNKNOWN"
            # If none have upload_time, fall back to best effort.
            return prefetched_versions[0].license or "UNKNOWN"

        try:
            return self.version_set.latest().license
        except Version.DoesNotExist:
            return "UNKNOWN"

    def grids(self):
        return (x.grid for x in self.gridpackage_set.all())

    def repo_name(self):
        return self.repo.extract_repo_name(self.repo_url)

    def repo_info(self):
        return dict(
            username=self.repo_name().split("/")[0],
            repo_name=self.repo_name().split("/")[1],
        )

    def participant_list(self):
        return [
            participant
            for p in self.participants.split(",")
            if (participant := p.strip())
        ]

    def get_usage_count(self):
        return self.usage.count()

    def commits_over_52(self):
        cache_name = self.cache_namer(self.commits_over_52)
        value = cache.get(cache_name)
        if value is not None:
            return value

        if self.commits_over_52w:
            return ",".join(map(str, self.commits_over_52w))

        reference_now = now()
        cutoff = reference_now - timedelta(weeks=52)

        # Prefer a view-provided prefetch of recent commits.
        prefetched_recent_commits = getattr(self, "_prefetched_commits_52w", None)
        if prefetched_recent_commits is None and hasattr(
            self, "_prefetched_objects_cache"
        ):
            prefetched_recent_commits = self._prefetched_objects_cache.get("commit_set")

        if prefetched_recent_commits is not None:
            commit_dates = [
                c.commit_date
                for c in prefetched_recent_commits
                if c.commit_date > cutoff
            ]
        else:
            commit_dates = self.commit_set.filter(
                commit_date__gt=cutoff,
            ).values_list("commit_date", flat=True)

        weeks = [0] * 52
        for cdate in commit_dates:
            age_weeks = (reference_now - cdate).days // 7
            if age_weeks < 52:
                weeks[age_weeks] += 1

        value = ",".join(map(str, reversed(weeks)))
        cache.set(cache_name, value)
        return value

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
    def development_status(self):
        """Gets data needed in API v2 calls"""
        if release := self.last_released():
            return release.pretty_status
        return None

    @property
    def pypi_ancient(self):
        if release := self.last_released():
            return release.upload_time < now() - timedelta(365)
        return None

    @property
    def no_development(self):
        commit_date = self.last_updated()
        if commit_date is not None:
            return commit_date < now() - timedelta(365)
        return None

    @property
    def last_commit(self):
        prefetched_commits = getattr(self, "_prefetched_commits_52w", None)
        if prefetched_commits:
            return prefetched_commits[0]
        return self.commit_set.latest()

    def commits_over_52_listed(self):
        return [int(x) for x in self.commits_over_52().split(",")]


class FlaggedPackage(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="flags")
    reason = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    approved_flag = models.BooleanField(default=False)

    def approve(self):
        self.approved_flag = True
        self.save()

    class Meta:
        ordering = ["-created"]
        UniqueConstraint(fields=["package", "user"], name="unique_flagged_package")

    def __str__(self):
        return f"{self.package.repo_name} - {self.reason}"


class PackageExample(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    title = models.CharField(_("Title"), max_length=100)
    url = models.URLField(_("URL"))
    active = models.BooleanField(
        _("Active"),
        default=None,
        help_text="Moderators have to approve links before they are provided",
        null=True,
    )
    created_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def pretty_url(self):
        if self.url.startswith("http"):
            return self.url
        return "http://" + self.url


class Commit(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    commit_date = models.DateTimeField(_("Commit Date"))
    commit_hash = models.CharField(
        _("Commit Hash"),
        help_text="Example: Git sha or SVN commit id",
        max_length=150,
        blank=True,
        default="",
    )

    class Meta:
        ordering = ["-commit_date"]
        get_latest_by = "commit_date"

    def __str__(self):
        return f"Commit for '{self.package.title}' on {self.commit_date}"

    def save(self, *args, **kwargs):
        # reset the last_updated and commits_over_52 caches on the package
        package = self.package
        cache.delete(package.cache_namer(self.package.last_updated))
        cache.delete(package.cache_namer(package.commits_over_52))
        self.package.last_updated()
        super().save(*args, **kwargs)


class VersionManager(models.Manager):
    def by_version(self, visible=False, *args, **kwargs):
        qs = self.get_queryset().filter(*args, **kwargs)

        if visible:
            qs = qs.filter(hidden=False)

        def generate_valid_versions(qs):
            for item in qs:
                v = LooseVersion(item.number)
                comparable = True
                for elem in v.version:
                    if isinstance(elem, str):
                        comparable = False
                if comparable:
                    yield item

        return sorted(
            # list(qs), # TODO: Add back...
            list(
                generate_valid_versions(qs)
            ),  # this would remove ["2.1.0.beta3", "2.1.0.rc1",]
            key=lambda v: LooseVersion(v.number),
        )

    def by_version_not_hidden(self, *args, **kwargs):
        return list(reversed(self.by_version(visible=True, *args, **kwargs)))


class Version(BaseModel):
    package = models.ForeignKey(
        Package, blank=True, null=True, on_delete=models.CASCADE
    )
    number = models.CharField(_("Version"), max_length=100, default="", blank="")
    downloads = models.IntegerField(_("downloads"), default=0)
    license = models.CharField(_("license"), max_length=100, null=True, blank=True)
    licenses = ArrayField(
        models.CharField(max_length=100, verbose_name=_("licenses")),
        null=True,
        blank=True,
        help_text="Comma separated list of licenses.",
    )
    hidden = models.BooleanField(_("hidden"), default=False)
    upload_time = models.DateTimeField(
        _("upload_time"),
        help_text=_("When this was uploaded to PyPI"),
        blank=True,
        null=True,
    )
    development_status = models.IntegerField(
        _("Development Status"), choices=PackageStatus.choices, default=0
    )
    supports_python3 = models.BooleanField(_("Supports Python 3"), default=False)

    objects = VersionManager()

    class Meta:
        get_latest_by = "upload_time"
        ordering = ["-upload_time"]

    @property
    def pretty_license(self):
        return self.license.replace("License", "").replace("license", "")

    @property
    def pretty_status(self):
        return self.get_development_status_display().split(" ")[-1]

    def save(self, *args, **kwargs):
        self.license = normalize_license(self.license)

        if not self.upload_time:
            self.upload_time = self.created

        # reset the latest_version cache on the package
        cache_name = self.package.cache_namer(self.package.last_released)
        cache.delete(cache_name)
        get_version(self.package)

        # reset the pypi_version cache on the package
        cache_name = self.package.cache_namer(self.package.pypi_version)
        cache.delete(cache_name)
        get_pypi_version(self.package)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.package.title}: {self.number}"
