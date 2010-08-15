from django.forms import ModelForm

from grid.models import Grid

class GridForm(ModelForm):
    
    class Meta:
        model = Grid
        fields = ['title', 'slug', 'description']
