from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from profiles.models import Profile


class ProfileForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        
        fields = (
                    'bitbucket_url',
                    'google_code_url',
                    )
        model = Profile
