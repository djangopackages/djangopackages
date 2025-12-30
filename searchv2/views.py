from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import F, FloatField, Q
from django.db.models.functions import Cast, Round
from django.http import (
    JsonResponse,
)
from django.utils.translation import gettext as _
from django.views.generic import ListView, TemplateView, View

from homepage.views import HomepageView
from searchv2.builders import build_1
from searchv2.forms import SearchForm
from searchv2.models import SearchV2
from searchv2.utils import clean_title, remove_prefix


class BuildSearchView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "new/build_search.html"

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        results = build_1()
        msg = f"{len(results)} {_('Items In Search')}"
        messages.success(request, msg)
        return self.render_to_response(self.get_context_data(results=results))


def search_function(q: str, max_weight: int = 1):
    """TODO - make generic title searches have lower weight"""
    items = []
    if q:
        items = (
            SearchV2.objects.filter(
                Q(clean_title__startswith=clean_title(remove_prefix(q)))
                | Q(title__icontains=q)
                | Q(title_no_prefix__startswith=q.lower())
                | Q(slug__startswith=q.lower())
                | Q(slug_no_prefix__startswith=q.lower())
                | Q(description__icontains=q)
            )
            .annotate(weight_as_float=Cast("weight", output_field=FloatField()))
            .annotate(
                weight_percent=(
                    Round(F("weight_as_float") / float(max_weight) * 100, precision=2)
                )
            )
        )
    return items


# def search(request, template_name="searchv2/search.html"):
#     """
#     Searches in Grids and Packages
#     """
#     q = request.GET.get("q", "")

#     if "/" in q:
#         lst = q.split("/")
#         try:
#             if lst[-1]:
#                 q = lst[-1]
#             else:
#                 q = lst[-2]
#         except IndexError:
#             pass
#     try:
#         package = Package.objects.get(title=q)
#         url = reverse("package", args=[package.slug.lower()])
#         return HttpResponseRedirect(url)
#     except Package.DoesNotExist:
#         pass
#     except Package.MultipleObjectsReturned:
#         pass

#     try:
#         package = Package.objects.get(slug=q)
#         url = reverse("package", args=[package.slug.lower()])
#         return HttpResponseRedirect(url)
#     except Package.DoesNotExist:
#         pass
#     except Package.MultipleObjectsReturned:
#         pass

#     form = SearchForm(request.GET or None)

#     return render(
#         request,
#         template_name,
#         {
#             "items": search_function(q),
#             "form": form,
#             "max_weight": SearchV2.objects.all().aggregate(Max("weight"))[
#                 "weight__max"
#             ],
#         },
#     )


def search2(request, template_name="searchv2/search.html"):
    """
    Searches in Grids and Packages
    """
    return HomepageView.as_view(template_name=template_name)(request)


class SearchSuggestionsView(ListView):
    model = SearchV2
    template_name = "new/partials/suggestions.html"
    context_object_name = "search_results"
    paginate_by = 10

    def get_queryset(self):
        self.form = SearchForm(self.request.GET)
        if self.form.is_valid():
            q = self.form.cleaned_data["q"]
            return search_function(q)
        return SearchV2.objects.none()

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


# def search3(request, template_name="search/search.html"):
#     """
#     Searches in Grids and Packages
#     """

#     if q := request.GET.get("q", ""):
#         query = q
#     elif q := request.GET.get("term", ""):
#         query = q
#     elif q := request.GET.get("search", ""):
#         query = q
#     else:
#         query = ""

#     if "/" in query:
#         lst = query.split("/")
#         try:
#             if lst[-1]:
#                 query = lst[-1]
#             else:
#                 query = lst[-2]
#         except IndexError:
#             pass

#     if request.htmx:
#         template_name = "search/search_partial.html"
#     else:
#         template_name = "search/search.html"

#         try:
#             package = Package.objects.get(title=q)
#             url = reverse("package", args=[package.slug.lower()])
#             return HttpResponseRedirect(url)
#         except (Package.DoesNotExist, Package.MultipleObjectsReturned):
#             pass

#         try:
#             package = Package.objects.get(slug=q)
#             url = reverse("package", args=[package.slug.lower()])
#             return HttpResponseRedirect(url)
#         except (Package.DoesNotExist, Package.MultipleObjectsReturned):
#             pass

#     max_weight = SearchV2.objects.only("weight").aggregate(max_weight=Max("weight"))[
#         "max_weight"
#     ]

#     return render(
#         request,
#         template_name,
#         {
#             "items": search_function(query, max_weight=max_weight or 1)[:20],
#         },
#     )


class OpenSearchDescription(TemplateView):
    template_name = "search_description.xml"


class OpenSearchSuggestions(View):
    def get(self, request):
        suggestions = []
        q = request.GET.get("q", "")
        results = search_function(q)[:15]
        suggestions.append(q)
        titles = []
        links = []
        for result in results:
            titles.append(result.title)
            links.append(result.absolute_url)
        suggestions.append(titles)
        suggestions.append([])
        suggestions.append(links)
        return JsonResponse(suggestions, safe=False)
