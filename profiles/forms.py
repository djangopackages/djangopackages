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
        widgets = {
            "label": forms.TextInput(
                attrs={"placeholder": "Label", "class": "textinput form-control"},
            ),
            "url": forms.TextInput(
                attrs={"placeholder": "URL", "class": "textinput form-control"}
            ),
        }


ExtraFieldFormSet = forms.inlineformset_factory(
    Profile,
    ExtraField,
    form=ExtraFieldForm,
    extra=4,
    max_num=4,
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
