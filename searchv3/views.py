from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.generic import ListView, TemplateView, View

from searchv3.builders import build_search_index
from searchv3.forms import SearchForm
from searchv3.models import SearchV3


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


class OpenSearchDescription(TemplateView):
    template_name = "search_description.xml"


class OpenSearchSuggestions(View):
    def get(self, request):
        q = request.GET.get("q", "")
        results = SearchV3.objects.search(q)[:15]

        titles = [r.title for r in results]
        links = [str(r.get_absolute_url()) for r in results]

        return JsonResponse([q, titles, [], links], safe=False)
