from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, ButtonHolder, Fieldset, Layout, Submit
from django import forms

from profiles.models import Profile


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
                "extra_field_label_01",
                "extra_field_content_01",
                "extra_field_label_02",
                "extra_field_content_02",
                "extra_field_label_03",
                "extra_field_content_03",
                "extra_field_label_04",
                "extra_field_content_04",
            ),
            ButtonHolder(Submit("edit", "Edit", css_class="btn btn-default")),
        )

    class Meta:
        fields = (
            "bitbucket_url",
            "gitlab_url",
            "extra_field_label_01",
            "extra_field_content_01",
            "extra_field_label_02",
            "extra_field_content_02",
            "extra_field_label_03",
            "extra_field_content_03",
            "extra_field_label_04",
            "extra_field_content_04",
        )
        model = Profile
