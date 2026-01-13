"""Forms for the :mod:`grid` app"""

from django.forms import (
    # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
    # BooleanField,
    ChoiceField,
    Form,
    ModelForm,
    CharField,
    IntegerField,
)
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


class GridDetailFilterForm(Form):
    """Filter and sort form for grid detail view"""

    SCORE = "score"
    # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
    # COMMIT_DATE = "commit_date"
    WATCHERS = "watchers"
    DOWNLOADS = "downloads"
    FORKS = "forks"
    TITLE = "title"

    SORT_CHOICES = (
        (SCORE, _("Score")),
        (TITLE, _("Name")),
        # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
        # (COMMIT_DATE, _("Last Commit")),
        (WATCHERS, _("Stars")),
        (DOWNLOADS, _("Downloads")),
        (FORKS, _("Forks")),
    )

    # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
    # python3 = BooleanField(required=False, label=_("Python 3 Only"))
    # stable = BooleanField(required=False, label=_("Stable Only"))
    sort = ChoiceField(
        choices=SORT_CHOICES, initial=SCORE, required=False, label=_("Sort by")
    )
    q = CharField(required=False, label=_("Search"))


class GridFilterForm(Form):
    SORT_CHOICES = (
        ("-modified", _("Updated (Desc)")),
        ("modified", _("Updated (Asc)")),
        ("-title", _("Title (Desc)")),
        ("title", _("Title (Asc)")),
        ("-gridpackage_count", _("Total Packages (Desc)")),
        ("gridpackage_count", _("Total Packages (Asc)")),
        ("-active_gridpackage_count", _("Active Packages (Desc)")),
        ("active_gridpackage_count", _("Active Packages (Asc)")),
    )

    q = CharField(required=False)
    sort = ChoiceField(choices=SORT_CHOICES, required=False, initial="-modified")
    page = IntegerField(required=False, min_value=1)
