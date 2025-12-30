from django import forms
from django.forms import ModelForm, TextInput
from django.utils.translation import gettext_lazy as _

from package.models import Category, FlaggedPackage, Package, PackageExample


def package_help_text():
    help_text = "".join(
        (
            """<li><strong>{title_plural}</strong> {description}</li>""".format(
                title_plural=category.title_plural,
                description=category.description,
            )
        )
        for category in Category.objects.all()
    )

    help_text = f"<ul>{help_text}</ul>"
    return help_text


class PackageForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].help_text = package_help_text()
        self.fields["repo_url"].required = True
        self.fields["repo_url"].widget = TextInput(
            attrs={"placeholder": "ex: https://github.com/django/django"}
        )

    def clean_slug(self):
        return self.cleaned_data["slug"].lower()

    class Meta:
        model = Package
        fields = [
            "repo_url",
            "repo_host",
            "title",
            "slug",
            "pypi_url",
            "category",
            "documentation_url",
        ]


class FlaggedPackageForm(ModelForm):
    class Meta:
        model = FlaggedPackage
        fields = ["reason"]


class PackageExampleForm(ModelForm):
    class Meta:
        model = PackageExample
        fields = ["title", "url"]


class PackageExampleModeratorForm(ModelForm):
    class Meta:
        model = PackageExample
        fields = ["title", "url", "active"]


class DocumentationForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["documentation_url"].widget.attrs.update(
            {
                "placeholder": "https://example.com/docs",
            }
        )

    class Meta:
        model = Package
        fields = [
            "documentation_url",
        ]


class BasePackageFilterForm(forms.Form):
    SORT_CHOICES = (
        ("-repo_watchers", _("Stars (Desc)")),
        ("repo_watchers", _("Stars (Asc)")),
        ("-repo_forks", _("Forks (Desc)")),
        ("repo_forks", _("Forks (Asc)")),
        ("-pypi_downloads", _("Downloads (Desc)")),
        ("pypi_downloads", _("Downloads (Asc)")),
        ("-last_fetched", _("Last Updated (Desc)")),
        ("last_fetched", _("Last Updated (Asc)")),
        ("title", _("Title (Asc)")),
        ("-title", _("Title (Desc)")),
        ("category", _("Category (Asc)")),
        ("-category", _("Category (Desc)")),
        ("-usage_count", _("Usage Count (Desc)")),
        ("usage_count", _("Usage Count (Asc)")),
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES, required=False, initial="-repo_watchers"
    )
    page = forms.IntegerField(required=False, min_value=1)
    q = forms.CharField(required=False)


class PackageFilterForm(BasePackageFilterForm):
    category = forms.CharField(required=False)


class CategoryPackageFilterForm(BasePackageFilterForm):
    pass
