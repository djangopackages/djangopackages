from django.forms import ModelForm

from grid.models import Grid, Element, Feature

class GridForm(ModelForm):
    
    class Meta:
        model = Grid
        fields = ['title', 'slug', 'description']

class ElementForm(ModelForm):

    class Meta:
        model = Element
        fields = ['text',]

class FeatureForm(ModelForm):

    class Meta:
        model = Feature
        fields = ['title', 'description',]