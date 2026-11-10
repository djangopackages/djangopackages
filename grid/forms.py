"""Forms for the :mod:`grid` app"""

from django.forms import (
    BooleanField,
    ChoiceField,
    Form,
    ModelForm,
    CharField,
    IntegerField,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from grid.feature_types import FeatureType, hint
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

    The text is checked against the feature's type, so a yes / no
    feature will not take "maybe" and a URL feature will not take prose.
    A text feature, the default, still takes anything.
    """

    class Meta:
        model = Element
        fields = [
            "text",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        feature = getattr(self.instance, "feature", None)
        if feature is not None and feature.type != FeatureType.TEXT:
            self.fields["text"].help_text = hint(feature.type)
            if feature.type == FeatureType.CHOICE and feature.choices:
                self.fields["text"].help_text += " " + ", ".join(feature.choices)

    def clean_text(self):
        text = self.cleaned_data["text"]
        feature = getattr(self.instance, "feature", None)
        if feature is not None and not feature.parse(text).ok:
            raise ValidationError(
                _('This does not read as "%(type)s".')
                % {"type": feature.get_type_display()}
            )
        return text


class FeatureForm(ModelForm):
    """collects data for the feature -
    a ``ModelForm`` for :class:`grid.models.Feature`

    `choices` is stored as a JSON list but typed as one line of
    comma-separated values, which is what a grid editor expects.
    """

    choice_list = CharField(
        label=_("Choices"),
        required=False,
        help_text=_(
            'For "one of a list" features: the allowed values, separated by commas.'
        ),
    )

    class Meta:
        model = Feature
        fields = [
            "title",
            "description",
            "type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional in the post, so the forms and API clients that only
        # ever sent a title and description keep working. Missing means
        # text, the same as the model default.
        self.fields["type"].required = False
        if self.instance.pk and self.instance.choices:
            self.fields["choice_list"].initial = ", ".join(self.instance.choices)

    def clean(self):
        cleaned = super().clean()
        cleaned["type"] = cleaned.get("type") or FeatureType.TEXT
        raw = cleaned.get("choice_list", "")
        choices = [part.strip() for part in raw.split(",") if part.strip()]
        if cleaned.get("type") == FeatureType.CHOICE and not choices:
            self.add_error(
                "choice_list", _('A "one of a list" feature needs its choices.')
            )
        cleaned["choice_list"] = choices
        return cleaned

    def save(self, commit=True):
        self.instance.choices = self.cleaned_data.get("choice_list", [])
        return super().save(commit=commit)


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
    COMMIT_DATE = "commit_date"
    WATCHERS = "watchers"
    DOWNLOADS = "downloads"
    FORKS = "forks"
    TITLE = "title"

    SORT_CHOICES = (
        (SCORE, _("Score")),
        (TITLE, _("Name")),
        (COMMIT_DATE, _("Last Commit")),
        (WATCHERS, _("Stars")),
        (DOWNLOADS, _("Downloads")),
        (FORKS, _("Forks")),
    )
    stable = BooleanField(required=False, label=_("Stable Only"))
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
