from django.core.validators import URLValidator
from django.forms import ModelForm
from django.template.defaultfilters import slugify

from package.models import Package, PackageExample

class PackageForm(ModelForm):
    
    def clean_slug(self):
        return self.cleaned_data['slug'].lower()
                
    class Meta:
        model = Package
        fields = ['repo_url', 'title', 'slug', 'pypi_url', 'category', ]
        
        
class PackageExampleForm(ModelForm):

    class Meta:
        model = PackageExample
        fields = ['title', 'url']        
        
class PackageExampleModeratorForm(ModelForm):

    class Meta:
        model = PackageExample
        fields = ['title', 'url', 'active']
