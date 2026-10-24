from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, F
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.generic import ListView, TemplateView, View

from searchv3.builders import build_search_index
from searchv3.forms import SearchForm, SearchResultsForm
from searchv3.models import ItemType, SearchV3


class BuildSearchView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "searchv3/build_search.html"

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        build_search_index()
        msg = f"{_('Search index built successfully.')}"
        messages.success(request, msg)
        return self.render_to_response(self.get_context_data(**kwargs))


class SearchSuggestionsView(ListView):
    model = SearchV3
    template_name = "partials/suggestions.html"
    context_object_name = "search_results"
    paginate_by = 10

    def get_queryset(self):
        self.form = SearchForm(self.request.GET)
        if self.form.is_valid():
            q = self.form.cleaned_data["q"]
            return SearchV3.objects.search(q)
        return SearchV3.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context["page_obj"]
        paginator = context["paginator"]

        context.update(
            {
                "query": self.request.GET.get("q", ""),
                "total_count": paginator.count,
                "shown_count": page_obj.end_index(),
                "has_more": page_obj.has_next(),
                "next_page": (
                    page_obj.next_page_number() if page_obj.has_next() else None
                ),
                "dropdown_id": self.request.GET.get(
                    "dropdown_id", "suggestions-dropdown"
                ),
                "is_load_more": self.request.GET.get("load_more") == "1",
            }
        )
        return context


# How each sort orders the matches. Relevance stays the tiebreaker so two
# packages with the same star count keep their search order.
SORTS = {
    "relevance": ("-relevance", "-similarity", "title"),
    "stars": ("-repo_watchers", "-relevance", "title"),
    "downloads": ("-pypi_downloads", "-relevance", "title"),
    "released": (F("last_released").desc(nulls_last=True), "-relevance", "title"),
    "committed": (F("last_committed").desc(nulls_last=True), "-relevance", "title"),
}


class SearchResultsView(ListView):
    """The full results page, with filters on top of the ranked matches.

    The filters never touch the ranking: `search()` decides what matches
    and how well, and the view narrows and reorders that set. They are
    plain GET parameters, so a filtered page can be shared and comes
    back the same.
    """

    model = SearchV3
    template_name = "searchv3/results.html"
    context_object_name = "search_results"
    paginate_by = 20

    def get_queryset(self):
        self.form = SearchResultsForm(self.request.GET)
        if not self.form.is_valid():
            self.filters = {"q": "", "type": "all", "category": "", "sort": "relevance"}
            self.matches = SearchV3.objects.none()
            return self.matches

        self.filters = self.form.cleaned_data
        self.matches = SearchV3.objects.search(self.filters["q"])

        queryset = self.matches
        if self.filters["type"] != "all":
            queryset = queryset.filter(item_type=self.filters["type"])
        if self.filters["category"]:
            queryset = queryset.filter(category=self.filters["category"])
        return queryset.order_by(*SORTS[self.filters["sort"]])

    def _url(self, **changes):
        """This page's URL with some parameters changed. Page resets."""
        params = {
            "q": self.filters["q"],
            "type": self.filters["type"],
            "category": self.filters["category"],
            "sort": self.filters["sort"],
        }
        params.update(changes)
        kept = {
            key: value
            for key, value in params.items()
            if value and value not in ("all", "relevance")
        }
        return f"{self.request.path}?{urlencode(kept)}"

    def _counts(self, field):
        """Matches per value of `field`, before this view's filters."""
        # Group over the matching rows by primary key: the search
        # annotations (relevance, similarity) would otherwise land in the
        # GROUP BY and give one row per match.
        rows = (
            SearchV3.objects.filter(pk__in=self.matches.values("pk"))
            .values(field)
            .annotate(n=Count("pk"))
            .order_by("-n", field)
        )
        return {row[field]: row["n"] for row in rows if row[field]}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.filters["q"]
        context["current_type"] = self.filters["type"]
        context["current_category"] = self.filters["category"]
        context["current_sort"] = self.filters["sort"]
        context["page_url"] = self._url()

        if not self.filters["q"]:
            return context

        by_type = self._counts("item_type")
        context["type_filters"] = [
            {
                "value": value,
                "label": label,
                "count": sum(by_type.values())
                if value == "all"
                else by_type.get(value, 0),
                "active": value == self.filters["type"],
                # Switching type drops the category, since grids have none.
                "url": self._url(type=value, category=""),
            }
            for value, label in SearchResultsForm.TYPE_CHOICES
        ]

        # Categories only mean something for packages.
        if self.filters["type"] != ItemType.GRID:
            by_category = self._counts("category")
            context["category_filters"] = [
                {
                    "value": "",
                    "label": _("All categories"),
                    "count": sum(by_category.values()),
                    "active": not self.filters["category"],
                    "url": self._url(category=""),
                }
            ] + [
                {
                    "value": name,
                    "label": name,
                    "count": count,
                    "active": name == self.filters["category"],
                    "url": self._url(category=name),
                }
                for name, count in by_category.items()
            ]

        context["sort_options"] = [
            {
                "value": value,
                "label": label,
                "active": value == self.filters["sort"],
                "url": self._url(sort=value),
            }
            for value, label in SearchResultsForm.SORT_CHOICES
        ]
        return context


class OpenSearchDescription(TemplateView):
    template_name = "search_description.xml"


class OpenSearchSuggestions(View):
    def get(self, request):
        q = request.GET.get("q", "")
        results = SearchV3.objects.search(q)[:15]

        titles = [r.title for r in results]
        links = [str(r.get_absolute_url()) for r in results]

        return JsonResponse([q, titles, [], links], safe=False)
