from django import forms
from django.utils.translation import gettext_lazy as _

from searchv3.models import ItemType


class SearchForm(forms.Form):
    """Simple q based search form"""

    q = forms.CharField(label="Search Grids and Packages", max_length=100)


class SearchResultsForm(SearchForm):
    """The full results page: the query plus the filters that narrow it.

    Every field is optional and a bad value falls back to its default, so
    a hand edited URL still returns results rather than a form error.
    """

    TYPE_CHOICES = (
        ("all", _("All")),
        (ItemType.PACKAGE, _("Packages")),
        (ItemType.GRID, _("Grids")),
    )
    SORT_CHOICES = (
        ("relevance", _("Relevance")),
        ("stars", _("Stars")),
        ("downloads", _("Downloads")),
        ("released", _("Recently released")),
        ("committed", _("Recently committed")),
    )

    # Plain CharFields rather than ChoiceFields: an unknown value should
    # fall back to the default, not make the whole form invalid and
    # return no results.
    type = forms.CharField(required=False)
    category = forms.CharField(required=False, max_length=50)
    sort = forms.CharField(required=False)

    def clean_type(self):
        value = self.cleaned_data.get("type")
        return value if value in dict(self.TYPE_CHOICES) else "all"

    def clean_sort(self):
        value = self.cleaned_data.get("sort")
        return value if value in dict(self.SORT_CHOICES) else "relevance"

    def clean_category(self):
        return (self.cleaned_data.get("category") or "").strip()
