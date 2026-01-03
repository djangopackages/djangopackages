from django import forms

from profiles.models import Profile, ExtraField


class ExtraFieldForm(forms.ModelForm):
    class Meta:
        model = ExtraField
        fields = (
            "label",
            "url",
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        fields = (
            "bitbucket_url",
            "gitlab_url",
            "share_favorites",
        )
        model = Profile
