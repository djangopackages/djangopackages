from django.forms import ModelForm

from package.models import Package, PackageExample

class PackageForm(ModelForm):
    
    class Meta:
        model = Package
        fields = ['title', 'slug', 'category', 'repo', 'repo_url', 'pypi_url']
        
class PackageExampleForm(ModelForm):

    class Meta:
        model = PackageExample
        fields = ['title', 'url']        
        
class PackageExampleModeratorForm(ModelForm):

    class Meta:
        model = PackageExample
        fields = ['title', 'url', 'active']        