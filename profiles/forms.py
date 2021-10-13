from django import forms

from profiles.models import Profile

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = "profile_edit"
        self.helper.layout = Layout(
            Fieldset(
                "",
                HTML(
                    """
                    <p>Github account, <strong>{{ profile.github_account }}</strong></p>
                """
                ),
                "bitbucket_url",
                "google_code_url",
            ),
            ButtonHolder(Submit("edit", "Edit", css_class="btn btn-default")),
        )

    class Meta:
        fields = (
            "bitbucket_url",
            "google_code_url",
        )
        model = Profile
