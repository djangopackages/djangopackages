from django import forms


class SearchForm(forms.Form):
    """Simple q based search form"""

    q = forms.CharField(label="Search Grids and Packages", max_length=100)
