"""Roll-ups over the probe profiles, for the stats page.

Every figure here is a single query over ``probes_packageprobe``, because
the JSON lists unnest in SQL: ``jsonb_array_elements`` turns one row's
symbol list into rows, so "how many packages use this" is a GROUP BY
rather than a loop in Python. The alternative, columns per symbol, would
need a migration every time Django grew an API.

The queries scan the whole table, so each one is cached. Nothing here is
live data: a probe profile only changes when a scan runs, and the
commands that write one call `invalidate()` when they finish.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import django
from django.core.cache import cache
from django.db import connection
from packaging.version import InvalidVersion, Version

from probes import removals
from probes.models import SETTINGS_PREFIX, ProbeSymbol
from probes.version_support import FRAMEWORK_CLASSIFIERS

CACHE_SECONDS = 60 * 15
GENERATION_KEY = "probe-stats:generation"

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
    # The top-level import a symbol belongs to, so the symbols table can
    # be filtered down to one library once scans count more than Django.
    library: str = ""

    def share(self, total: int) -> float:
        return (self.packages / total * 100) if total else 0.0


@dataclass
class Totals:
    probed: int = 0
    scanned: int = 0
    with_python: int = 0
    with_django: int = 0
    with_wagtail: int = 0
    with_django_cms: int = 0
    with_dependencies: int = 0
    files_scanned: int = 0
    distinct_symbols: int = 0
    distinct_settings: int = 0
    distinct_patterns: int = 0
    total_uses: int = 0
    # Distinct removed APIs something still uses. Symbols, not packages:
    # one package calling three of them counts three times here.
    removed_symbols: int = 0
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
        result.with_wagtail,
        result.with_django_cms,
        result.with_dependencies,
        result.files_scanned,
    ) = _query(
        """
        SELECT count(*),
               count(*) FILTER (WHERE scanned_at IS NOT NULL),
               count(*) FILTER (WHERE jsonb_array_length(python_versions) > 0),
               count(*) FILTER (WHERE jsonb_array_length(django_versions) > 0),
               count(*) FILTER (WHERE framework_versions ? 'wagtail'),
               count(*) FILTER (WHERE framework_versions ? 'django-cms'),
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


def framework_version_rows(framework: str) -> list[Row]:
    """How many packages claim each cycle of a framework in framework_versions.

    The column is one JSON object keyed by framework, so the cycles come
    out of `->` rather than straight from the column.
    """
    if framework not in FRAMEWORK_CLASSIFIERS:
        raise ValueError(framework)
    rows = _query(
        """
        SELECT cycle, count(DISTINCT p.package_id)
        FROM probes_packageprobe p,
             jsonb_array_elements_text(p.framework_versions -> %s) AS cycle
        GROUP BY 1
        """,
        [framework],
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
               coalesce(sym->>'library', split_part(sym->>'symbol', '.', 1)),
               count(DISTINCT p.package_id),
               coalesce(sum((sym->>'count')::bigint), 0)
        FROM probes_packageprobe p, jsonb_array_elements(p.symbols) AS sym
        WHERE sym->>'symbol' NOT LIKE %s
        GROUP BY 1, 2 ORDER BY 3 DESC, 4 DESC, 1
        """,
        [f"{SETTINGS_PREFIX}%"],
    )
    return [
        Row(label=label, library=library, packages=n, uses=uses)
        for label, library, n, uses in rows
    ]


def symbol_libraries(rows: list[Row]) -> list[Row]:
    """The libraries these symbols belong to, most symbols first.

    `packages` on each returned row is how many symbols, since that is
    what the filter button narrows the table to and what the "All"
    button counts. Django first when it is there, because it is the
    one everyone came to see.
    """
    counts: dict[str, Row] = {}
    for row in rows:
        if not row.library:
            continue
        found = counts.setdefault(row.library, Row(label=row.library, packages=0))
        found.packages += 1
        found.uses += row.uses
    return sorted(
        counts.values(), key=lambda row: (row.label != "django", -row.packages)
    )


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

    `packages` on each returned row holds how many table rows, which
    are symbols, carry that version. That is the number the filter
    button shows, and it matches the "All" button, which counts rows too.
    """
    counts: dict[str, Row] = {}
    for row in rows:
        if not row.note:
            continue
        found = counts.setdefault(row.note, Row(label=row.note, packages=0))
        found.packages += 1
        found.uses += row.uses
    return _sorted_by_version(list(counts.values()))


def _generation() -> int:
    """Which round of data the cached roll-ups belong to.

    Kept with no expiry. If the cache drops it anyway, the new value is
    the time, so it cannot land back on a number some stale entry
    still answers to.
    """
    return cache.get_or_set(GENERATION_KEY, time.time_ns, timeout=None)


def invalidate() -> None:
    """Start a new round, so every roll-up is rebuilt on next read.

    Called by whatever writes profiles or curation. Cheaper than
    counting the table on every read, and unlike a count it notices a
    rescan that changed rows without adding any.
    """
    cache.set(GENERATION_KEY, time.time_ns(), timeout=None)


def cached(name: str, builder):
    """One cache entry per roll-up, since each is a full table scan."""
    key = f"probe-stats:{name}:{_generation()}"
    value = cache.get(key)
    if value is None:
        value = builder()
        cache.set(key, value, CACHE_SECONDS)
    return value
