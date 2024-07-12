"""Forms for the :mod:`grid` app"""

from crispy_forms.helper import FormHelper
from django.forms import BooleanField, ChoiceField, Form, ModelForm
from django.utils.translation import gettext_lazy as _

from grid.models import Element, Feature, Grid, GridPackage


class GridForm(ModelForm):
    """collects data for the new grid - a
    django ``ModelForm`` for :class:`grid.models.Grid`
    """

    def clean_slug(self):
        """returns lower-cased slug"""
        return self.cleaned_data["slug"].lower()

    class Meta:
        model = Grid
        fields = ["title", "slug", "description"]


class ElementForm(ModelForm):
    """collects data for a new grid element -
    a ``ModelForm`` for :class:`grid.models.Element`
    """

    class Meta:
        model = Element
        fields = [
            "text",
        ]


class FeatureForm(ModelForm):
    """collects data for the feature -
    a ``ModelForm`` for :class:`grid.models.Feature`
    """

    class Meta:
        model = Feature
        fields = [
            "title",
            "description",
        ]


class GridPackageForm(ModelForm):
    """collects data for a new package -
    a ``ModelForm`` for :class:`grid.models.GridPackage`
    """

    class Meta:
        model = GridPackage
        fields = ["package"]


class GridPackageFilterForm(Form):
    """Filter and sort form for the grid package list"""

    SCORE = "score"
    COMMIT_DATE = "commit_date"
    WATCHERS = "watchers"
    DOWNLOADS = "downloads"
    FORKS = "forks"

    SORT_CHOICES = (
        (SCORE, _("Score")),
        (COMMIT_DATE, _("Last Commit Date")),
        (WATCHERS, _("Watchers")),
        (DOWNLOADS, _("Downloads")),
        (FORKS, _("Forks")),
    )

    python3 = BooleanField(required=False, label=_("Python 3"))
    stable = BooleanField(required=False)
    sort = ChoiceField(
        choices=SORT_CHOICES, initial=SCORE, required=False, label=_("Sort by")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_class = "form-inline"
