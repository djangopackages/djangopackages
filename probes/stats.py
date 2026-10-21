"""Roll-ups over the probe profiles, for the stats page.

Every figure here is a single query over ``probes_packageprobe``, because
the JSON lists unnest in SQL: ``jsonb_array_elements`` turns one row's
symbol list into rows, so "how many packages use this" is a GROUP BY
rather than a loop in Python. The alternative, columns per symbol, would
need a migration every time Django grew an API.

The queries scan the whole table, so each one is cached. Nothing here is
live data: a probe profile only changes when a scan runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import django
from django.core.cache import cache
from django.db import connection
from packaging.version import InvalidVersion, Version

from probes import removals
from probes.models import PackageProbe, ProbeSymbol

CACHE_SECONDS = 60 * 15

# Vocabulary, so the page and the code agree on what to call things.
#
# symbol   one importable thing, written as its dotted path:
#          "django.db.models.CharField". Not a statement; a statement is
#          a line of Python, and the same symbol can appear in many.
# use      one reference to a symbol anywhere in the source.
# pattern  one of django-probe's named probes, which answers a question a
#          dotted path cannot, like whether transaction.atomic was a
#          decorator or a context manager.
# setting  a Django setting name read through django.conf.settings.
SETTINGS_PREFIX = "django.conf.settings."


@dataclass
class Row:
    """One line of a roll-up: a label, how many packages, how many uses."""

    label: str
    packages: int
    uses: int = 0
    extra: int = 0
    # A short string the roll-up wants to carry that is not a count,
    # such as the Django version that removed a symbol. Empty unless
    # the roll-up has something to say.
    note: str = ""

    def share(self, total: int) -> float:
        return (self.packages / total * 100) if total else 0.0


@dataclass
class Totals:
    probed: int = 0
    scanned: int = 0
    with_python: int = 0
    with_django: int = 0
    with_dependencies: int = 0
    files_scanned: int = 0
    distinct_symbols: int = 0
    distinct_settings: int = 0
    distinct_patterns: int = 0
    total_uses: int = 0
    unresolved_packages: int = 0
    django_version: str = field(default_factory=django.get_version)


def _query(sql: str, params=None) -> list[tuple]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        return cursor.fetchall()


def _sorted_by_version(rows: list[Row]) -> list[Row]:
    """Newest cycle first.

    Reading starts at the top, and what matters is who supports the
    current releases. Django 1.8 still shows up here and still belongs
    on the chart, just not above 6.0.
    """

    def key(row: Row):
        try:
            return Version(row.label)
        except InvalidVersion:
            return Version("0")

    return sorted(rows, key=key, reverse=True)


def totals() -> Totals:
    """The headline counts, in one pass over the table."""
    result = Totals()
    (
        result.probed,
        result.scanned,
        result.with_python,
        result.with_django,
        result.with_dependencies,
        result.files_scanned,
    ) = _query(
        """
        SELECT count(*),
               count(*) FILTER (WHERE scanned_at IS NOT NULL),
               count(*) FILTER (WHERE jsonb_array_length(python_versions) > 0),
               count(*) FILTER (WHERE jsonb_array_length(django_versions) > 0),
               count(*) FILTER (WHERE jsonb_array_length(dependencies) > 0),
               coalesce(sum(files_scanned), 0)
        FROM probes_packageprobe
        """
    )[0]

    result.distinct_symbols, result.total_uses = _query(
        """
        SELECT count(DISTINCT sym->>'symbol'),
               coalesce(sum((sym->>'count')::bigint), 0)
        FROM probes_packageprobe p, jsonb_array_elements(p.symbols) AS sym
        """
    )[0]
    result.distinct_settings = _query(
        """
        SELECT count(DISTINCT sym->>'symbol')
        FROM probes_packageprobe p, jsonb_array_elements(p.symbols) AS sym
        WHERE sym->>'symbol' LIKE %s
        """,
        [f"{SETTINGS_PREFIX}%"],
    )[0][0]
    result.distinct_patterns = _query(
        """
        SELECT count(DISTINCT pat->>'pattern')
        FROM probes_packageprobe p, jsonb_array_elements(p.patterns) AS pat
        """
    )[0][0]
    return result


def version_rows(column: str) -> list[Row]:
    """How many packages claim each cycle of python_versions/django_versions."""
    if column not in {"python_versions", "django_versions"}:
        raise ValueError(column)
    rows = _query(
        f"""
        SELECT cycle, count(DISTINCT p.package_id)
        FROM probes_packageprobe p,
             jsonb_array_elements_text(p.{column}) AS cycle
        GROUP BY 1
        """  # noqa: S608 - column is checked against a literal set above
    )
    return _sorted_by_version([Row(label=cycle, packages=n) for cycle, n in rows])


def source_rows(column: str) -> list[Row]:
    """Where each range came from, which is the honesty column.

    A range from `requires_dist` is inferred from a dependency pin, not
    claimed by the maintainer, so it deserves less trust than a
    classifier.
    """
    if column not in {"python_source", "django_source"}:
        raise ValueError(column)
    rows = _query(
        f"""
        SELECT CASE WHEN {column} = '' THEN 'none' ELSE {column} END, count(*)
        FROM probes_packageprobe
        GROUP BY 1 ORDER BY 2 DESC
        """  # noqa: S608 - column is checked against a literal set above
    )
    return [Row(label=label, packages=n) for label, n in rows]


def pattern_rows() -> list[Row]:
    rows = _query(
        """
        SELECT pat->>'pattern',
               count(DISTINCT p.package_id),
               coalesce(sum((pat->>'count')::bigint), 0)
        FROM probes_packageprobe p, jsonb_array_elements(p.patterns) AS pat
        GROUP BY 1 ORDER BY 2 DESC, 3 DESC, 1
        """
    )
    return [
        Row(label=label.removeprefix("probe:"), packages=n, uses=uses)
        for label, n, uses in rows
    ]


def setting_rows() -> list[Row]:
    rows = _query(
        """
        SELECT sym->>'symbol',
               count(DISTINCT p.package_id),
               coalesce(sum((sym->>'count')::bigint), 0)
        FROM probes_packageprobe p, jsonb_array_elements(p.symbols) AS sym
        WHERE sym->>'symbol' LIKE %s
        GROUP BY 1 ORDER BY 2 DESC, 3 DESC, 1
        """,
        [f"{SETTINGS_PREFIX}%"],
    )
    return [
        Row(label=label.removeprefix(SETTINGS_PREFIX), packages=n, uses=uses)
        for label, n, uses in rows
    ]


def library_rows() -> list[Row]:
    """Which libraries the scanned source actually uses.

    `extra` carries how many profiles went looking for that library, so
    a small number reads as "few packages use it" rather than "few scans
    asked". Older rows have no stored library, so the top-level import is
    taken off the symbol for them.
    """
    looked = dict(
        _query(
            """
            SELECT library, count(*)
            FROM probes_packageprobe p,
                 jsonb_array_elements_text(p.libraries) AS library
            GROUP BY 1
            """
        )
    )
    rows = _query(
        """
        SELECT coalesce(sym->>'library', split_part(sym->>'symbol', '.', 1)) AS library,
               count(DISTINCT p.package_id),
               coalesce(sum((sym->>'count')::bigint), 0)
        FROM probes_packageprobe p, jsonb_array_elements(p.symbols) AS sym
        GROUP BY 1 ORDER BY 2 DESC, 3 DESC, 1
        """
    )
    return [
        Row(label=label, packages=n, uses=uses, extra=looked.get(label, 0))
        for label, n, uses in rows
    ]


def symbol_rows() -> list[Row]:
    """Symbols by how many packages use them, not by raw count.

    One package calling something four hundred times should not outrank
    forty packages calling it once. Settings have their own table, so
    they are left out here rather than counted twice.
    """
    rows = _query(
        """
        SELECT sym->>'symbol',
               count(DISTINCT p.package_id),
               coalesce(sum((sym->>'count')::bigint), 0)
        FROM probes_packageprobe p, jsonb_array_elements(p.symbols) AS sym
        WHERE sym->>'symbol' NOT LIKE %s
        GROUP BY 1 ORDER BY 2 DESC, 3 DESC, 1
        """,
        [f"{SETTINGS_PREFIX}%"],
    )
    return [Row(label=label, packages=n, uses=uses) for label, n, uses in rows]


def dependency_rows() -> list[Row]:
    """Declared dependencies, with how many need them for a plain install."""
    rows = _query(
        """
        SELECT dep->>'name',
               count(DISTINCT p.package_id),
               count(DISTINCT p.package_id) FILTER (WHERE dep->>'extra' = '')
        FROM probes_packageprobe p, jsonb_array_elements(p.dependencies) AS dep
        GROUP BY 1 ORDER BY 2 DESC, 1
        """
    )
    return [Row(label=label, packages=n, extra=required) for label, n, required in rows]


def unresolved_rows() -> list[Row]:
    """Symbols the packages use that Django has since removed.

    This is the half of a probe that metadata cannot give you. A package
    whose classifiers claim Django 5.2 while its source calls
    `ugettext_lazy` is telling you two different things, and only one of
    them was tested.

    A row appears only when `probes.removals` can name the version that
    removed it, or when somebody has curated the catalogue to say so.
    We used to ask the installed Django instead, by importing each
    dotted path and calling whatever failed removed. Two in five of the
    rows that produced were wrong, because plenty of live APIs do not
    import here: anything under `django.contrib.gis` without GDAL, a
    database backend whose driver we skip, an app that is not in
    INSTALLED_APPS.
    """
    curated = dict(
        ProbeSymbol.objects.filter(kind=ProbeSymbol.Kind.SYMBOL)
        .exclude(removed_in="")
        .values_list("name", "removed_in")
    )

    gone = []
    for row in symbol_rows():
        version = curated.get(row.label) or removals.removed_in(row.label)
        if version:
            row.note = version
            gone.append(row)
    return gone


def removal_versions(rows: list[Row]) -> list[Row]:
    """The Django versions these rows were removed in, newest first.

    Only versions something actually hit, so the filter never offers a
    release that would come back empty. Rows we have no removal version
    for are not counted here; they are still in the table.
    """
    counts: dict[str, Row] = {}
    for row in rows:
        if not row.note:
            continue
        found = counts.setdefault(row.note, Row(label=row.note, packages=0))
        found.packages += 1
        found.uses += row.uses
    return _sorted_by_version(list(counts.values()))


def cached(name: str, builder):
    """One cache entry per roll-up, since each is a full table scan."""
    key = f"probe-stats:{name}:{PackageProbe.objects.count()}"
    value = cache.get(key)
    if value is None:
        value = builder()
        cache.set(key, value, CACHE_SECONDS)
    return value
