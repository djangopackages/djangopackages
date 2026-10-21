"""What probing a package turned up, and what we know about each API.

Two tables. ``PackageProbe`` is one row per package: the versions it
claims, what its source uses, and when we last looked. ``ProbeSymbol``
is one row per thing a scan can name, which is where a deprecation or a
removal version belongs, since that is a fact about the API rather than
about any package that calls it.

The flags that decide whether a package gets probed at all stay on
``package.Package``, because they describe the package.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class PackageProbe(BaseModel):
    """What probing a package turned up, in the spirit of django-probe.

    One row per package, holding the two things a probe can learn about
    it: the versions it claims to support, and what its source actually
    uses. Kept out of Package because it is derived data with its own
    refresh cycle, and because a probe that goes wrong should be
    throwable away without touching the package itself.

    The lists are JSON rather than columns because they are read as
    whole documents. Postgres can still answer "who depends on X" over
    them with jsonb_array_elements, so grouping is a query away rather
    than a schema change.
    """

    class Source(models.TextChoices):
        CLASSIFIERS = "classifiers", _("Trove classifiers")
        REQUIRES_PYTHON = "requires_python", _("requires_python")
        REQUIRES_DIST = "requires_dist", _("requires_dist")

    package = models.OneToOneField(
        "package.Package", on_delete=models.CASCADE, related_name="probe_profile"
    )

    python_versions = models.JSONField(
        _("Python versions"),
        default=list,
        blank=True,
        help_text=_('Cycles this package claims, oldest first: ["3.10", "3.11"]'),
    )
    django_versions = models.JSONField(
        _("Django versions"),
        default=list,
        blank=True,
        help_text=_('Cycles this package claims, oldest first: ["5.1", "5.2"]'),
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

    dependencies = models.JSONField(
        _("Dependencies"),
        default=list,
        blank=True,
        help_text=_(
            "One object per declared dependency, as "
            '{"name", "specifier", "extra", "marker"}. An extra means it is '
            "optional, which is kept rather than dropped because what anyone "
            "depends on and what a default install pulls in are different "
            "questions."
        ),
    )

    symbols = models.JSONField(
        _("symbol usage"),
        default=list,
        blank=True,
        help_text=_(
            "What the AST scan counted, most used first, as "
            '[{"symbol": "django.conf.settings", "count": 16, '
            '"library": "django"}]. A list rather than a mapping so it '
            "keeps that order, and so a dotted path stays a value "
            "instead of becoming a key. The library is the top-level "
            "import, stored so grouping by it is a plain GROUP BY."
        ),
    )
    patterns = models.JSONField(
        _("pattern hits"),
        default=list,
        blank=True,
        help_text=_(
            "django-probe's named probes, most hit first, as "
            '[{"pattern": "probe:queryset_filter", "count": 12}]. These '
            "say what a dotted path cannot: whether transaction.atomic "
            "was a decorator or a context manager, or whether a class "
            "subclasses AbstractUser."
        ),
    )
    libraries = models.JSONField(
        _("libraries scanned for"),
        default=list,
        blank=True,
        help_text=_(
            'The top-level imports the scan looked for, as ["django"]. '
            "Kept because a profile with no symbols from a library means "
            "nothing unless we know the scan asked about it."
        ),
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

    @property
    def symbol_counts(self) -> dict[str, int]:
        """The symbol list as a mapping, for when a lookup is what you want."""
        return {row["symbol"]: row["count"] for row in self.symbols}

    @property
    def library_counts(self) -> dict[str, int]:
        """Uses per library, most used first."""
        totals: dict[str, int] = {}
        for row in self.symbols:
            library = row.get("library") or row["symbol"].partition(".")[0]
            totals[library] = totals.get(library, 0) + row["count"]
        return dict(sorted(totals.items(), key=lambda item: -item[1]))

    @property
    def pattern_counts(self) -> dict[str, int]:
        """The pattern list as a mapping."""
        return {row["pattern"]: row["count"] for row in self.patterns}

    @property
    def settings_used(self) -> dict[str, int]:
        """Named Django settings the source reads, without the prefix.

        Derived from the symbol list rather than stored again. A setting
        django-probe does not recognise folds to a bare
        `django.conf.settings`, so what is left here is real setting
        names, and the bare path still counts the rest.
        """
        prefix = "django.conf.settings."
        return {
            row["symbol"].removeprefix(prefix): row["count"]
            for row in self.symbols
            if row["symbol"].startswith(prefix)
        }

    @property
    def required(self) -> list[dict]:
        """Dependencies a plain install pulls in."""
        return [d for d in self.dependencies if not d.get("extra")]

    @property
    def optional(self) -> list[dict]:
        """Dependencies that only apply behind an extra."""
        return [d for d in self.dependencies if d.get("extra")]


class ProbeSymbol(BaseModel):
    """One thing a scan can name, with what we know about it.

    PackageProbe answers "what does this package use". This answers
    "what is this thing, and should anyone still be using it", which is
    a property of the API rather than of any one package, so it lives in
    its own table with one row per library and name.

    The counts are derived and get replaced wholesale by
    build_probe_catalog. The curation below them is ours and is never
    overwritten by a rebuild: a rebuild that forgot a deprecation would
    be worse than no catalogue at all.
    """

    class Kind(models.TextChoices):
        SYMBOL = "symbol", _("Symbol")
        PATTERN = "pattern", _("Pattern")
        SETTING = "setting", _("Setting")

    kind = models.CharField(
        _("kind"), max_length=10, choices=Kind.choices, default=Kind.SYMBOL
    )
    library = models.CharField(
        _("library"),
        max_length=100,
        default="django",
        help_text=_("The top-level import this belongs to."),
    )
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_(
            "The dotted path for a symbol, the setting name for a "
            "setting, or the probe key for a pattern."
        ),
    )

    packages = models.IntegerField(_("packages using it"), default=0)
    uses = models.BigIntegerField(_("total uses"), default=0)
    counted_at = models.DateTimeField(_("counts last rebuilt"), blank=True, null=True)

    deprecated = models.BooleanField(_("deprecated"), default=False)
    deprecated_in = models.CharField(
        _("deprecated in"),
        max_length=20,
        blank=True,
        default="",
        help_text=_("The library version that deprecated it, like 3.1."),
    )
    removed_in = models.CharField(
        _("removed in"),
        max_length=20,
        blank=True,
        default="",
        help_text=_("The library version that removed it, like 4.0."),
    )
    notes = models.TextField(_("notes"), blank=True, default="")

    class Meta:
        verbose_name = _("Probe symbol")
        verbose_name_plural = _("Probe symbols")
        ordering = ["-packages", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "library", "name"], name="unique_probe_symbol"
            )
        ]
        indexes = [
            models.Index(fields=["library", "kind"]),
            models.Index(fields=["deprecated"]),
        ]

    def __str__(self):
        return self.name

    @property
    def gone(self) -> bool:
        """Whether anyone should still be reaching for this."""
        return bool(self.removed_in)

    @property
    def status(self) -> str:
        if self.removed_in:
            return f"removed in {self.removed_in}"
        if self.deprecated_in:
            return f"deprecated in {self.deprecated_in}"
        if self.deprecated:
            return "deprecated"
        return ""


class Library(BaseModel):
    """A distribution name and the name you actually import.

    `pip install django-debug-toolbar` then `import debug_toolbar`. The
    two names agree often enough to be lulling and differ often enough
    to be a bug: djangorestframework imports as rest_framework, Pillow
    as PIL, django-q2 as django_q. A scan that guesses by replacing
    hyphens with underscores quietly finds nothing for those.

    The import name is what a symbol's `library` holds, so this is the
    table that joins a probe result back to something installable.
    """

    class Source(models.TextChoices):
        CHECKOUT = "checkout", _("Read from the checkout")
        MANUAL = "manual", _("Entered by hand")

    pypi_name = models.CharField(
        _("PyPI name"),
        max_length=255,
        unique=True,
        help_text=_("What you pip install, like django-debug-toolbar."),
    )
    import_name = models.CharField(
        _("import name"),
        max_length=255,
        db_index=True,
        help_text=_("What you import, like debug_toolbar."),
    )
    also_imports = models.JSONField(
        _("other import names"),
        default=list,
        blank=True,
        help_text=_(
            "Further top-level imports the same distribution ships, as "
            '["a", "b"]. Most have none.'
        ),
    )
    source = models.CharField(
        _("where the import name came from"),
        max_length=10,
        choices=Source.choices,
        default=Source.CHECKOUT,
    )
    package = models.ForeignKey(
        "package.Package",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="probe_libraries",
        help_text=_("The package we index for this distribution, if we index it."),
    )
    scan = models.BooleanField(
        _("scan for this library"),
        blank=True,
        null=True,
        default=None,
        help_text=_(
            "Toggle on to have scans count this library's usage as well "
            "as Django's. Null means nobody has decided, which reads as "
            "off: every library added here is counted in every file of "
            "every checkout, so it is opt in."
        ),
    )
    notes = models.TextField(_("notes"), blank=True, default="")

    class Meta:
        verbose_name = _("Library")
        verbose_name_plural = _("Libraries")
        ordering = ["pypi_name"]

    def __str__(self):
        if self.import_name == self.pypi_name:
            return self.pypi_name
        return f"{self.pypi_name} ({self.import_name})"

    @property
    def names_differ(self) -> bool:
        """Whether swapping hyphens for underscores would have got it wrong.

        Nothing is stored from that: it decides which rows are worth
        printing when the table is rebuilt, since those are the ones
        anyone matching names by hand would trip over.
        """
        return self.import_name != self.pypi_name.replace("-", "_").lower()

    @property
    def import_names(self) -> list[str]:
        """Every top-level import this distribution ships."""
        return [self.import_name, *self.also_imports]

    @classmethod
    def scan_for(cls) -> tuple[str, ...]:
        """The import names scans should count, Django first.

        Only the primary import name of each library that has been
        toggled on. The extra names a distribution ships are usually
        its demo project or its test app, which nobody depends on.
        """
        names = cls.objects.filter(scan=True).values_list("import_name", flat=True)
        ordered = sorted(set(names), key=lambda name: (name != "django", name))
        return tuple(ordered)
