import json

from django.contrib.auth.decorators import login_required
from django.db.models import F, FloatField, Max, Q
from django.db.models.functions import Cast, Round
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View, TemplateView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from homepage.views import homepage
from package.models import Package
from searchv2.builders import build_1
from searchv2.forms import SearchForm
from searchv2.models import SearchV2
from searchv2.utils import clean_title, remove_prefix


@login_required
def build_search(request, template_name="searchv2/build_results.html"):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    results = []
    if request.method == "POST":
        results = build_1()

    return render(request, template_name, {"results": results})


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
            )
            .annotate(weight_as_float=Cast("weight", output_field=FloatField()))
            .annotate(
                weight_percent=(
                    Round(F("weight_as_float") / float(max_weight) * 100, precision=2)
                )
            )
        )
    return items


def search(request, template_name="searchv2/search.html"):
    """
    Searches in Grids and Packages
    """
    q = request.GET.get("q", "")

    if "/" in q:
        lst = q.split("/")
        try:
            if lst[-1]:
                q = lst[-1]
            else:
                q = lst[-2]
        except IndexError:
            pass
    try:
        package = Package.objects.get(title=q)
        url = reverse("package", args=[package.slug.lower()])
        return HttpResponseRedirect(url)
    except Package.DoesNotExist:
        pass
    except Package.MultipleObjectsReturned:
        pass

    try:
        package = Package.objects.get(slug=q)
        url = reverse("package", args=[package.slug.lower()])
        return HttpResponseRedirect(url)
    except Package.DoesNotExist:
        pass
    except Package.MultipleObjectsReturned:
        pass

    form = SearchForm(request.GET or None)

    return render(
        request,
        template_name,
        {
            "items": search_function(q),
            "form": form,
            "max_weight": SearchV2.objects.all().aggregate(Max("weight"))[
                "weight__max"
            ],
        },
    )


def search2(request, template_name="searchv2/search.html"):
    """
    Searches in Grids and Packages
    """
    return homepage(request, template_name=template_name)


def search3(request, template_name="search/search.html"):
    """
    Searches in Grids and Packages
    """

    if q := request.GET.get("q", ""):
        query = q
    elif q := request.GET.get("term", ""):
        query = q
    elif q := request.GET.get("search", ""):
        query = q
    else:
        query = ""

    if "/" in query:
        lst = query.split("/")
        try:
            if lst[-1]:
                query = lst[-1]
            else:
                query = lst[-2]
        except IndexError:
            pass

    if request.htmx:
        template_name = "search/search_partial.html"
    else:
        template_name = "search/search.html"

        try:
            package = Package.objects.get(title=q)
            url = reverse("package", args=[package.slug.lower()])
            return HttpResponseRedirect(url)
        except (Package.DoesNotExist, Package.MultipleObjectsReturned):
            pass

        try:
            package = Package.objects.get(slug=q)
            url = reverse("package", args=[package.slug.lower()])
            return HttpResponseRedirect(url)
        except (Package.DoesNotExist, Package.MultipleObjectsReturned):
            pass

    max_weight = SearchV2.objects.only("weight").aggregate(max_weight=Max("weight"))[
        "max_weight"
    ]

    return render(
        request,
        template_name,
        {
            "items": search_function(query, max_weight=max_weight or 1)[:20],
        },
    )


def search_packages_autocomplete(request):
    """
    Searches in Packages
    """
    q = request.GET.get("term", "")
    if q:
        objects = search_function(q)[:15]
        objects = objects.values_list("title", flat=True)
        json_response = json.dumps(list(objects))
    else:
        json_response = json.dumps([])

    return HttpResponse(json_response, content_type="text/javascript")


class SearchListAPIView(ListAPIView):
    model = SearchV2
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        return search_function(q)


class SearchDetailAPIView(RetrieveAPIView):
    model = SearchV2


class OpenSearchDescription(TemplateView):
    template_name = "search_description.xml"


class OpenSearchSuggestions(View):
    def get(self, request):
        suggestions = []
        q = request.GET.get("q", "")
        print(q, "query")
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
