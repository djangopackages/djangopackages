"""Flag PyPI candidates that look like spam, junk or a removed project.

`screen(candidate, context)` returns the reason codes that fire. A strong
reason on its own, or two weak ones, moves a `new` row to `held` so it
leaves the review queue until a person looks. Informational reasons are
recorded for the reviewer but never count: a brand-new package is not
suspicious by itself, and nearly every one also has no traction yet; a
repository newer than the first release is mostly an old project that
moved hosts. Nothing here rejects: a
rejected name is never offered again, and that call stays with a person.

Every rule reads data already on the row (the BigQuery columns, the
trimmed PyPI JSON, the ecosyste.ms record) plus a `Context` of facts
across all candidates, such as how many names were first uploaded in the
same minute. No rule downloads or runs package code. See #1838.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from probes.models import Candidate

STRONG, WEAK, INFO = "strong", "weak", "info"

# code -> (label shown in the admin, weight)
REASONS: dict[str, tuple[str, str]] = {
    "removed-from-pypi": ("PyPI no longer has this project", STRONG),
    "misspelled-django": ("Name misspells django", STRONG),
    "release-flood": ("15+ releases, four or more a week", STRONG),
    "no-framework-dependency": (
        "No django, wagtail or django-cms in requires_dist",
        WEAK,
    ),
    "no-repository": ("No repository link", WEAK),
    "repository-unknown": ("ecosyste.ms cannot see the repository", WEAK),
    "repository-unrelated": (
        "Repository name shares nothing with the package name",
        WEAK,
    ),
    "repository-fork": ("Repository is a fork", WEAK),
    "repository-after-release": (
        "Repository created a month or more after the first release",
        INFO,
    ),
    "has-advisories": ("Has security advisories", WEAK),
    "no-traction": ("No stars, dependents or downloads", WEAK),
    "placeholder-summary": ("Summary is empty or a placeholder", WEAK),
    "upload-burst": ("First uploaded in the same minute as 2+ other candidates", WEAK),
    "author-burst": ("Same author email as 2+ other candidates new this quarter", WEAK),
    "brand-new": ("First upload in the last 30 days", INFO),
}

MISSPELLED_DJANGO = re.compile(r"djnago|djagno|dajngo|djanog|djangoo|jdango|djngo")
PLACEHOLDER_SUMMARIES = {"", "add your description here", "tbc", "tbd", "todo", "test"}
FLOOD_RELEASES = 15
FLOOD_SPAN = timedelta(days=120)
FLOOD_PER_WEEK = 4
NEW_WINDOW = timedelta(days=30)
AUTHOR_WINDOW = timedelta(days=90)
BURST_SIZE = 3
LATE_REPOSITORY = timedelta(days=30)
LOW_DOWNLOADS = 50
GENERIC_WORDS = {"django", "py", "python", "wagtail", "cms", "djangocms", "drf"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


@dataclass
class Context:
    """Facts that need every candidate at once."""

    now: datetime = field(default_factory=timezone.now)
    uploads_per_minute: Counter = field(default_factory=Counter)
    new_names_per_email: Counter = field(default_factory=Counter)

    @classmethod
    def build(cls, candidates, *, now: datetime | None = None) -> Context:
        context = cls(now=now or timezone.now())
        for candidate in candidates:
            if candidate.first_upload:
                context.uploads_per_minute[minute(candidate.first_upload)] += 1
            if is_recent(candidate, context.now - AUTHOR_WINDOW):
                for email in emails(candidate):
                    context.new_names_per_email[email] += 1
        return context

    @classmethod
    def from_database(cls) -> Context:
        rows = Candidate.objects.only("first_upload", "pypi_data")
        return cls.build(rows.iterator(chunk_size=2000))


def minute(when: datetime) -> str:
    return when.astimezone(UTC).strftime("%Y-%m-%d %H:%M")


def emails(candidate: Candidate) -> set[str]:
    info = candidate.info
    text = f"{info.get('author_email') or ''} {info.get('maintainer_email') or ''}"
    return {email.lower() for email in EMAIL.findall(text)}


def is_recent(candidate: Candidate, since: datetime) -> bool:
    first = parse(candidate.first_release) or candidate.first_upload
    return bool(first and first >= since)


def parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def is_removed(candidate: Candidate) -> bool:
    """PyPI answered 404: we asked, and got nothing back."""
    return bool(candidate.pypi_fetched_at) and not candidate.pypi_data


def release_flood(candidate: Candidate) -> bool:
    dates = sorted(filter(None, map(parse, candidate.release_dates.values())))
    if len(dates) < FLOOD_RELEASES:
        return False
    span = dates[-1] - dates[0]
    weeks = max(span / timedelta(weeks=1), 1)
    return span <= FLOOD_SPAN and len(dates) / weeks >= FLOOD_PER_WEEK


def words(name: str) -> set[str]:
    return set(re.split(r"[-_.]+", name.lower())) - GENERIC_WORDS - {""}


def repository_unrelated(candidate: Candidate) -> bool:
    full_name = candidate.repo.get("full_name") or ""
    repo_name = full_name.rsplit("/", 1)[-1].lower().replace("_", "-")
    name = candidate.name.lower().replace("_", "-").replace(".", "-")
    if not repo_name or name in repo_name or repo_name in name:
        return False
    return not words(name) & words(repo_name)


def screen(candidate: Candidate, context: Context) -> list[str]:
    """Reason codes for one candidate, in the order of `REASONS`."""
    fired = set()
    name = candidate.name.lower()

    if is_removed(candidate):
        fired.add("removed-from-pypi")
    if MISSPELLED_DJANGO.search(name):
        fired.add("misspelled-django")
    if candidate.summary.strip().lower().rstrip(".") in PLACEHOLDER_SUMMARIES or (
        candidate.summary.strip().lower().replace("_", "-") == name.replace("_", "-")
    ):
        fired.add("placeholder-summary")
    if candidate.first_upload and candidate.first_upload >= context.now - NEW_WINDOW:
        fired.add("brand-new")
    if (
        candidate.first_upload
        and context.uploads_per_minute[minute(candidate.first_upload)] >= BURST_SIZE
    ):
        fired.add("upload-burst")

    if candidate.pypi_data:
        if release_flood(candidate):
            fired.add("release-flood")
        if candidate.depends_on_django is False:
            fired.add("no-framework-dependency")
        if not candidate.repo_url:
            fired.add("no-repository")
        if is_recent(candidate, context.now - AUTHOR_WINDOW) and any(
            context.new_names_per_email[email] >= BURST_SIZE
            for email in emails(candidate)
        ):
            fired.add("author-burst")

    if candidate.ecosystems_data:
        if candidate.advisories:
            fired.add("has-advisories")
        repo = candidate.repo
        if candidate.repo_url and not repo:
            fired.add("repository-unknown")
        if repo:
            if repo.get("fork"):
                fired.add("repository-fork")
            if repository_unrelated(candidate):
                fired.add("repository-unrelated")
            created = parse(repo.get("created_at"))
            first = parse(candidate.first_release)
            if created and first and created - first >= LATE_REPOSITORY:
                fired.add("repository-after-release")
        if (
            not candidate.stars
            and not candidate.dependents
            and (candidate.downloads or 0) < LOW_DOWNLOADS
        ):
            fired.add("no-traction")

    return [code for code in REASONS if code in fired]


def weight(code: str) -> str:
    return REASONS.get(code, ("", INFO))[1]


def should_hold(reasons: list[str]) -> bool:
    weights = [weight(code) for code in reasons]
    return STRONG in weights or weights.count(WEAK) >= 2


def label(code: str) -> str:
    return REASONS.get(code, (code, False))[0]


def screenable():
    """Rows screening may change: undecided, and never touched by a person."""
    return Candidate.objects.filter(
        Q(status=Candidate.Status.NEW) | Q(status=Candidate.Status.HELD),
        reviewed_by__isnull=True,
    )


@dataclass
class Screened:
    seen: int = 0
    held: int = 0
    released: int = 0
    changed: int = 0
    by_reason: Counter = field(default_factory=Counter)


def screen_all(*, apply: bool, names=None, context: Context | None = None) -> Screened:
    """Screen every screenable row, or just `names`, and save if `apply`.

    A row held by an earlier pass goes back to `new` when its reasons no
    longer add up, for example once ecosyste.ms catches up with it.
    """
    context = context or Context.from_database()
    rows = screenable()
    if names is not None:
        rows = rows.filter(name__in=list(names))
    result = Screened()
    for candidate in rows.iterator(chunk_size=500):
        result.seen += 1
        reasons = screen(candidate, context)
        result.by_reason.update(reasons)
        status = Candidate.Status.HELD if should_hold(reasons) else Candidate.Status.NEW
        if status == Candidate.Status.HELD:
            result.held += 1
        elif candidate.status == Candidate.Status.HELD:
            result.released += 1
        if reasons == candidate.reasons and status == candidate.status:
            continue
        result.changed += 1
        if apply:
            candidate.reasons = reasons
            candidate.status = status
            candidate.save(update_fields=["reasons", "status", "modified"])
    return result
