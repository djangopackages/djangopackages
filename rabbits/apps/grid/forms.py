from django.forms import ModelForm

from grid.models import Grid, Element

class GridForm(ModelForm):
    
    class Meta:
        model = Grid
        fields = ['title', 'slug', 'description']

class ElementForm(ModelForm):

    class Meta:
        model = Element
        fields = ['text',]
