from django.forms import ModelForm

from package.models import Package

class PackageForm(ModelForm):
    
    class Meta:
        model = Package
        fields = ['title', 'slug', 'category', 'repo', 'repo_url', 'pypi_url']