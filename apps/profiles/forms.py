from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from profiles.models import Profile


class ProfileForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()

        if not email:
            self._errors["email"] = self.error_class(["Email is a required field"])
            return ""

        if User.objects.filter(email=email).exclude(username=self.instance.user.username):
            self._errors["email"] = self.error_class(["%s is already in use in the system" % email])
            return ""            

        return email

    class Meta:
        
        fields = (
                    'github_url',
                    'bitbucket_url',
                    'google_code_url',
                    'email',
                    )
        model = Profile
