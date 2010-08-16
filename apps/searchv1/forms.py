from django import forms

class SearchForm(forms.Form):
    
    q            = forms.CharField(label="Search Grids and Packages", max_length=100)
    #package      = forms.BooleanField(label="Search packages?", initial=True)
    #grid         = forms.BooleanField(label="Search packages?", initial=True)