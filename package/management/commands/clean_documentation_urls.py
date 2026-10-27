"""Clear documentation URLs that only lead back to the repository or PyPI.

The documentation link is for a place the package page does not already
take the reader. `package.utils.documentation_url_problem` says which
links fail that test; this clears them. Forms and the PyPI updater
apply the same rule to new values, so this is for what was saved
before the rule existed.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import djclick as click
from rich import print as rprint

from package.models import Package
from package.utils import documentation_url_problem


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--dry-run", is_flag=True, help="Report without writing")
@click.option(
    "--examples", default=5, show_default=True, help="Examples to print per reason"
)
def command(slugs: tuple[str, ...], dry_run: bool, examples: int):
    """Blank every documentation_url that is the repository, its README, or PyPI."""
    queryset = (
        Package.objects.exclude(documentation_url="")
        .exclude(documentation_url__isnull=True)
        .only("slug", "documentation_url", "repo_url")
        .order_by("slug")
    )
    if slugs:
        queryset = queryset.filter(slug__in=slugs)

    reasons: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    checked = cleared = 0

    for package in queryset.iterator(chunk_size=1000):
        checked += 1
        problem = documentation_url_problem(
            package.documentation_url, repo_url=package.repo_url
        )
        if not problem:
            continue
        reasons[problem] += 1
        if len(samples[problem]) < examples:
            samples[problem].append(f"{package.slug}  {package.documentation_url}")
        if dry_run:
            continue
        # update() so `modified` and the search index are left alone.
        Package.objects.filter(pk=package.pk).update(documentation_url="")
        cleared += 1

    for reason, count in reasons.most_common():
        rprint(f"[bold]{reason}[/bold]  {count:,}")
        for line in samples[reason]:
            rprint(f"    {line}")

    suffix = "  [dim](dry run)[/dim]" if dry_run else ""
    rprint(
        f"checked {checked:,}  would clear {sum(reasons.values()):,}  "
        f"cleared {cleared:,}{suffix}"
    )
