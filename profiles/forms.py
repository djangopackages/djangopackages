from django import forms

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
