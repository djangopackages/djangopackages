"""Forms for the :mod:`grid` app
"""

from django.forms import ModelForm

from grid.models import  Element, Feature, Grid, GridPackage


class GridForm(ModelForm):
    """collects data for the new grid - a
    django ``ModelForm`` for :class:`grid.models.Grid`
    """

    def clean_slug(self):
        """returns lower-cased slug"""
        return self.cleaned_data['slug'].lower()

    class Meta:
        model = Grid
        fields = ['title', 'slug', 'description']


class ElementForm(ModelForm):
    """collects data for a new grid element -
    a ``ModelForm`` for :class:`grid.models.Element`
    """

    class Meta:
        model = Element
        fields = ['text', ]


class FeatureForm(ModelForm):
    """collects data for the feature -
    a ``ModelForm`` for :class:`grid.models.Feature`
    """

    class Meta:
        model = Feature
        fields = ['title', 'description', ]


class GridPackageForm(ModelForm):
    """collects data for a new package -
    a ``ModelForm`` for :class:`grid.models.GridPackage`
    """

    class Meta:
        model = GridPackage
        fields = ['package']
