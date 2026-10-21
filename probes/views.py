"""The probe stats pages.

Unlisted rather than private. Nothing here is secret, and a password
would only stop us looking at it, so these are kept out of the nav and
the sitemap and marked noindex instead.

Two views over the same six tables: an overview that shows the head of
each, and a page per table that shows all of it with a search box. The
tables are defined once, in SECTIONS, so the two cannot drift.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from probes import stats as probe_stats
from probes.models import Library


def _totals():
    return probe_stats.cached("totals", probe_stats.totals)


def _unresolved_rows():
    return probe_stats.cached("unresolved", probe_stats.unresolved_rows)


def _gone_label():
    """Not named for a version: the table spans every release."""
    return _("APIs Django has removed")


@dataclass(frozen=True)
class SectionSpec:
    """One table, described once and rendered by both views.

    `columns` pairs each heading with the field it reads, so a table
    that wants "required by" in its third column gets that rather than
    whatever the third field happens to be.
    """

    param: str
    label: str | Callable[[], str]
    columns: tuple[tuple[str, str], ...]
    rows: Callable[[], list]

    # An optional filter offered on the section's own page. `facets`
    # returns one row per value worth offering, counted from the rows
    # themselves, so a value that nothing hits is never shown.
    facet_param: str = ""
    facet_label: str = ""
    facet_field: str = ""
    facets: Callable[[list], list] | None = None

    @property
    def heading(self) -> str:
        return self.label() if callable(self.label) else self.label

    @property
    def url(self) -> str:
        return reverse("probes:section", kwargs={"section": self.param})


SECTIONS: dict[str, SectionSpec] = {
    spec.param: spec
    for spec in (
        SectionSpec(
            param="libraries",
            label=_("Libraries used"),
            columns=(
                (_("Library"), "label"),
                (_("Packages"), "packages"),
                (_("Uses"), "uses"),
                (_("Scanned for"), "extra"),
            ),
            rows=lambda: probe_stats.cached("libraries", probe_stats.library_rows),
        ),
        SectionSpec(
            param="patterns",
            label=_("Patterns"),
            columns=(
                (_("Pattern"), "label"),
                (_("Packages"), "packages"),
                (_("Hits"), "uses"),
            ),
            rows=lambda: probe_stats.cached("patterns", probe_stats.pattern_rows),
        ),
        SectionSpec(
            param="settings",
            label=_("Settings read"),
            columns=(
                (_("Setting"), "label"),
                (_("Packages"), "packages"),
                (_("Uses"), "uses"),
            ),
            rows=lambda: probe_stats.cached("settings", probe_stats.setting_rows),
        ),
        SectionSpec(
            param="symbols",
            label=_("Symbols"),
            columns=(
                (_("Symbol"), "label"),
                (_("Packages"), "packages"),
                (_("Uses"), "uses"),
            ),
            rows=lambda: probe_stats.cached("symbols", probe_stats.symbol_rows),
        ),
        SectionSpec(
            param="deps",
            label=_("Declared dependencies"),
            columns=(
                (_("Package"), "label"),
                (_("Depended on by"), "packages"),
                (_("Required by"), "extra"),
            ),
            rows=lambda: probe_stats.cached(
                "dependencies", probe_stats.dependency_rows
            ),
        ),
        # Last, because it is the most opinionated table on the page and
        # the least use as an opening fact about what we scanned.
        SectionSpec(
            param="gone",
            label=_gone_label,
            columns=(
                (_("Symbol"), "label"),
                (_("Packages"), "packages"),
                (_("Uses"), "uses"),
                (_("Removed in"), "note"),
            ),
            rows=_unresolved_rows,
            facet_param="removed_in",
            facet_label=_("Removed in Django"),
            facet_field="note",
            facets=probe_stats.removal_versions,
        ),
    )
}


def search(rows, query: str) -> list:
    """Rows whose label contains the query, matched without case."""
    needle = query.strip().casefold()
    if not needle:
        return rows
    return [row for row in rows if needle in row.label.casefold()]


class SectionMixin:
    """Shared pagination for the overview and the per-table pages.

    Each table lives in an element whose id is this prefix plus its page
    parameter, which is also what htmx sends back in HX-Target. That
    header is how a view knows which table to re-render, so paging needs
    no extra query parameter and the URL we push stays the one a plain
    reload would need.
    """

    section_template_name = "probes/partials/section.html"
    SECTION_PREFIX = "probe-section-"

    def requested_section(self) -> str | None:
        """The page parameter of the one table htmx asked us to swap."""
        htmx = getattr(self.request, "htmx", None)
        target = (htmx.target or "") if htmx else ""
        if not target.startswith(self.SECTION_PREFIX):
            return None
        return target.removeprefix(self.SECTION_PREFIX)

    def build_section(self, spec, rows, *, param, per_page, label=None, url=""):
        """One paginated table, with the bar chart's scale worked out.

        The bars are drawn against the widest row on the page rather
        than the overall maximum, so a long tail is still readable
        instead of collapsing into nothing.
        """
        paginator = Paginator(rows, per_page)
        page = paginator.get_page(self.request.GET.get(param))
        widest = max((row.packages for row in page.object_list), default=0)

        def link(number):
            query = self.request.GET.copy()
            query[param] = number
            return f"{self.request.path}?{query.urlencode()}"

        fields = [field for _heading, field in spec.columns[1:]]

        return {
            "label": spec.heading if label is None else label,
            "columns": [heading for heading, _field in spec.columns],
            "param": param,
            "url": url,
            "dom_id": f"{self.SECTION_PREFIX}{param}",
            "page": page,
            "paginator": paginator,
            "rows": [
                {
                    "label": row.label,
                    "values": [getattr(row, field) for field in fields],
                    "width": (row.packages / widest * 100) if widest else 0,
                }
                for row in page.object_list
            ],
            "first_url": link(1) if page.number > 2 else "",
            "last_url": (
                link(paginator.num_pages)
                if page.number < paginator.num_pages - 1
                else ""
            ),
            "previous_url": link(page.previous_page_number())
            if page.has_previous()
            else "",
            "next_url": link(page.next_page_number()) if page.has_next() else "",
        }


class ProbeStatsView(SectionMixin, TemplateView):
    """Unlisted dashboard of what the probe profiles add up to.

    No login, because there is nothing here that is not already public
    once a package page shows it, and asking for a password would only
    stop us looking at it. Kept out of the nav and the sitemap, and
    noindex, because it is a working tool rather than a page for
    visitors.

    Every table is its own paginator with its own query parameter, so
    paging through the symbols does not reset the settings table.
    """

    template_name = "probes/stats.html"
    PER_PAGE = 25

    def get(self, request, *args, **kwargs):
        """Swap one table for htmx, render the whole page otherwise.

        The links are ordinary anchors with ordinary URLs, so without
        htmx they still load the page with that table on the asked-for
        page. htmx only saves the other five tables from being rebuilt
        and the browser from repainting the whole page.
        """
        param = self.requested_section()
        if param is None:
            return super().get(request, *args, **kwargs)
        if param not in SECTIONS:
            raise Http404(f"No probe stats section named {param!r}")

        spec = SECTIONS[param]
        section = self.build_section(
            spec, spec.rows(), param=param, per_page=self.PER_PAGE, url=spec.url
        )
        return render(request, self.section_template_name, {"section": section})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        counts = _totals()
        counts.unresolved_packages = len({row.label for row in _unresolved_rows()})

        context["totals"] = counts
        context["django_versions"] = probe_stats.cached(
            "django_versions", lambda: probe_stats.version_rows("django_versions")
        )
        context["python_versions"] = probe_stats.cached(
            "python_versions", lambda: probe_stats.version_rows("python_versions")
        )
        context["django_sources"] = probe_stats.cached(
            "django_source", lambda: probe_stats.source_rows("django_source")
        )
        context["python_sources"] = probe_stats.cached(
            "python_source", lambda: probe_stats.source_rows("python_source")
        )
        context["libraries"] = Library.objects.filter(scan=True).order_by("import_name")
        context["sections"] = [
            self.build_section(
                spec,
                spec.rows(),
                param=spec.param,
                per_page=self.PER_PAGE,
                url=spec.url,
            )
            for spec in SECTIONS.values()
        ]
        return context


class ProbeSectionView(SectionMixin, TemplateView):
    """One table on its own page: all of it, paginated, with a search box.

    The search is a plain substring match on the label done in Python
    rather than in SQL, because the rows it filters are already a cached
    list. Going back to the database to narrow a list we are holding
    would cost a full scan of the JSON to save a few microseconds of
    string matching.
    """

    template_name = "probes/section.html"
    PER_PAGE = 50
    PARAM = "page"

    def get_spec(self):
        try:
            return SECTIONS[self.kwargs["section"]]
        except KeyError:
            raise Http404(
                f"No probe stats section named {self.kwargs['section']!r}"
            ) from None

    def get(self, request, *args, **kwargs):
        """Swap the table for htmx, whether that was paging or searching."""
        spec = self.get_spec()
        if self.requested_section() != self.PARAM:
            return super().get(request, *args, **kwargs)
        return render(
            request, self.section_template_name, {"section": self.section(spec)}
        )

    def chosen_facet(self, spec) -> str:
        """The facet value asked for, if this section offers that filter."""
        if not spec.facet_param:
            return ""
        return self.request.GET.get(spec.facet_param, "")

    def visible_rows(self, spec) -> list:
        """The rows left after the facet filter and the search."""
        rows = spec.rows()
        chosen = self.chosen_facet(spec)
        if chosen:
            rows = [row for row in rows if getattr(row, spec.facet_field) == chosen]
        return search(rows, self.request.GET.get("q", ""))

    def section(self, spec):
        return self.build_section(
            spec,
            self.visible_rows(spec),
            param=self.PARAM,
            per_page=self.PER_PAGE,
            label="",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spec = self.get_spec()
        context["spec"] = spec
        context["heading"] = spec.heading
        context["query"] = self.request.GET.get("q", "")
        context["total_rows"] = len(spec.rows())
        context["section"] = self.section(spec)
        context["facets"] = self.facets(spec)
        context["facet_label"] = spec.facet_label
        context["facet_param"] = spec.facet_param
        context["chosen_facet"] = self.chosen_facet(spec)
        return context

    def facets(self, spec) -> list[dict]:
        """The filter buttons, each with the URL that applies it.

        Built from the unfiltered rows, so choosing one does not make
        the others disappear, and only from values something actually
        hit, so none of them leads to an empty table.
        """
        if spec.facets is None:
            return []

        chosen = self.chosen_facet(spec)

        def link(value):
            query = self.request.GET.copy()
            query.pop(self.PARAM, None)
            if value:
                query[spec.facet_param] = value
            else:
                query.pop(spec.facet_param, None)
            encoded = query.urlencode()
            return f"{self.request.path}?{encoded}" if encoded else self.request.path

        rows = spec.rows()
        buttons = [
            {
                "label": _("All"),
                "count": len(rows),
                "url": link(""),
                "chosen": not chosen,
            }
        ]
        buttons += [
            {
                "label": row.label,
                "count": row.packages,
                "url": link(row.label),
                "chosen": row.label == chosen,
            }
            for row in spec.facets(rows)
        ]
        return buttons
