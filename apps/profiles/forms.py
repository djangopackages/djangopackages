from django import forms
from django.utils.translation import ugettext_lazy as _

from profiles.models import Profile


class ProfileForm(forms.ModelForm):
    

    class Meta:
        
        fields = (
                    'github_url',
                    'bitbucket_url',
                    'google_code_url',
                    )
        model = Profile
