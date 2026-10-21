from datetime import timedelta
from functools import cached_property
from django.conf import settings
from django.contrib.auth.models import User

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
from package.utils import normalize_license

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
    slug = models.SlugField(_("slug"), unique=True)
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

    def get_opengraph_image_url(self):
        return reverse("category_opengraph", args=[self.slug])


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
        _("Documentation URL"), blank=True, null=True, default="", max_length=500
    )

    probe = models.BooleanField(
        _("Probe source"),
        blank=True,
        null=True,
        default=None,
        help_text=_(
            "Whether to keep a git checkout of this package and scan its "
            "source. Null means nobody has looked yet, which is where "
            "check_package_sources starts."
        ),
    )
    probe_checked_at = models.DateTimeField(
        _("date probe status was last checked"), blank=True, null=True
    )
    probe_note = models.CharField(
        _("why probing is off"), max_length=200, blank=True, default=""
    )

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

    @property
    def repo(self):
        return get_repo_for_repo_url(self.repo_url, self.repo_host or None)

    @property
    def active_examples(self):
        return self.packageexample_set.filter(active=True)

    def grids(self):
        return (x.grid for x in self.gridpackage_set.all() if x.grid.is_approved)

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

    @cached_property
    def commits_over_52w_str(self):
        if self.commits_over_52w:
            return ",".join(map(str, self.commits_over_52w))
        return ""

    @property
    def development_status(self):
        if version := self.latest_version:
            return version.development_status
        return None

    @property
    def latest_version_number(self):
        if version := self.latest_version:
            return version.number
        return None

    @property
    def pypi_ancient(self):
        if (version := self.latest_version) and version.upload_time:
            return version.upload_time < now() - timedelta(365)
        return None

    @property
    def no_development(self):
        commit_date = self.last_commit_date
        if commit_date:
            return commit_date < now() - timedelta(365)
        return None

    @property
    def pypi_license_display(self):
        return self.pypi_license or "UNKNOWN"


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
        constraints = [
            UniqueConstraint(
                fields=["package", "number"], name="unique_version_package_number"
            )
        ]

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

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.package.title}: {self.number}"


class PackageProbe(BaseModel):
    """What probing a package turned up, in the spirit of django-probe.

    One row per package, holding the two things a probe can learn about
    it: the versions it claims to support, and what its source actually
    uses. Kept out of Package because it is derived data with its own
    refresh cycle, and because a probe that goes wrong should be
    throwable away without touching the package itself.
    """

    class Source(models.TextChoices):
        CLASSIFIERS = "classifiers", _("Trove classifiers")
        REQUIRES_PYTHON = "requires_python", _("requires_python")
        REQUIRES_DIST = "requires_dist", _("requires_dist")

    package = models.OneToOneField(
        "package.Package", on_delete=models.CASCADE, related_name="probe_profile"
    )

    python_versions = ArrayField(
        models.CharField(max_length=10),
        default=list,
        blank=True,
        help_text=_("Python cycles this package claims, oldest first"),
    )
    django_versions = ArrayField(
        models.CharField(max_length=10),
        default=list,
        blank=True,
        help_text=_("Django cycles this package claims, oldest first"),
    )
    python_source = models.CharField(
        _("where the Python versions came from"),
        max_length=20,
        choices=Source,
        blank=True,
        default="",
    )
    django_source = models.CharField(
        _("where the Django versions came from"),
        max_length=20,
        choices=Source,
        blank=True,
        default="",
    )

    symbols = models.JSONField(
        _("symbol usage"),
        default=dict,
        blank=True,
        help_text=_("What the AST scan counted, as {dotted.path: uses}"),
    )
    files_scanned = models.IntegerField(default=0)
    files_skipped = models.IntegerField(default=0)
    commit = models.CharField(
        _("commit the scan read"), max_length=40, blank=True, default=""
    )

    metadata_updated_at = models.DateTimeField(blank=True, null=True)
    scanned_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _("Package probe")
        verbose_name_plural = _("Package probes")

    def __str__(self):
        return f"probe for {self.package.slug}"

    @property
    def python_range(self) -> str:
        return self._span(self.python_versions)

    @property
    def django_range(self) -> str:
        return self._span(self.django_versions)

    @staticmethod
    def _span(versions) -> str:
        if not versions:
            return ""
        if len(versions) == 1:
            return versions[0]
        return f"{versions[0]} - {versions[-1]}"


class PackageDependency(BaseModel):
    """One thing a package depends on.

    A row per dependency rather than a blob on the package, because the
    question worth asking is the other way round: which libraries does
    the catalogue lean on, and how hard. That is a group by, and a
    JSONField would make it a table scan.
    """

    class Source(models.TextChoices):
        DECLARED = "requires_dist", _("Declared in PyPI metadata")
        IMPORTED = "imports", _("Imported in the source")

    package = models.ForeignKey(
        "package.Package", on_delete=models.CASCADE, related_name="dependencies"
    )
    name = models.CharField(_("Dependency"), max_length=214, db_index=True)
    specifier = models.CharField(
        _("Version specifier"), max_length=120, blank=True, default=""
    )
    extra = models.CharField(
        _("Extra it belongs to"),
        max_length=100,
        blank=True,
        default="",
        help_text=_("Blank when it is a plain dependency"),
    )
    marker = models.CharField(
        _("Environment marker"), max_length=255, blank=True, default=""
    )
    source = models.CharField(
        max_length=20, choices=Source, default=Source.DECLARED, db_index=True
    )

    class Meta:
        verbose_name = _("Package dependency")
        verbose_name_plural = _("Package dependencies")
        constraints = [
            models.UniqueConstraint(
                fields=["package", "name", "extra", "source"],
                name="unique_package_dependency",
            )
        ]
        indexes = [models.Index(fields=["name", "source"])]

    def __str__(self):
        return f"{self.package.slug} -> {self.name}{self.specifier}"

    @property
    def is_optional(self) -> bool:
        return bool(self.extra)
