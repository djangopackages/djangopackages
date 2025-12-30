from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, ButtonHolder, Fieldset, Layout, Submit
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = "profile_edit"
        self.helper.layout = Layout(
            Fieldset(
                "",
                HTML(
                    """
                    <p>GitHub account, <strong>{{ profile.github_account }}</strong></p>
                """
                ),
                "bitbucket_url",
                "gitlab_url",
                "share_favorites",
            ),
            HTML("""{{ extra_fields_formset }}"""),
            ButtonHolder(Submit("edit", "Edit", css_class="btn btn-default")),
        )

    class Meta:
        fields = (
            "bitbucket_url",
            "gitlab_url",
            "share_favorites",
        )
        model = Profile
