from django import forms
from django.forms import ModelForm, TextInput
from django.utils.translation import gettext_lazy as _

from package.models import Category, FlaggedPackage, Package, PackageExample
from package.repos.repo_url_normelizer import normalize_repo_url


def package_help_text():
    rows = "".join(
        (
            """
            <tr class="border-b last:border-0">
                <td class="py-1 pr-4 font-semibold align-top whitespace-nowrap">
                    {title_plural}
                </td>
                <td class="py-1 align-top">
                    {description}
                </td>
            </tr>
            """.format(
                title_plural=category.title_plural,
                description=category.description,
            )
        )
        for category in Category.objects.all()
    )

    help_text = f'<table class="min-w-full text-sm mt-4"><tbody>{rows}</tbody></table>'
    return help_text


class RepositoryURLForm(forms.Form):
    repo_url = forms.CharField(
        label=_("Repository URL"),
        required=True,
        help_text=_(
            "Enter your project repository hosting URL here. Example: https://github.com/djangopackages/djangopackages."
        ),
        widget=TextInput(
            attrs={
                "placeholder": "ex: https://github.com/django/django",
            }
        ),
    )

    def clean_repo_url(self):
        value = self.cleaned_data["repo_url"]
        try:
            return normalize_repo_url(value)
        except Exception as e:
            raise forms.ValidationError(str(e))


class BasePackageForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].help_text = package_help_text()
        self.fields["repo_url"].required = True
        self.fields["repo_url"].label = _("Repository URL")
        self.fields["repo_url"].widget = TextInput(
            attrs={"placeholder": "ex: https://github.com/django/django"}
        )

    def clean_slug(self):
        return self.cleaned_data["slug"].lower()

    def clean_repo_url(self):
        value = self.cleaned_data["repo_url"]
        try:
            return normalize_repo_url(value)
        except Exception as e:
            raise forms.ValidationError(str(e))

    class Meta:
        model = Package
        fields = [
            "repo_url",
            "repo_host",
            "title",
            "slug",
            "pypi_url",
            "documentation_url",
            "category",
        ]

    def clean_pypi_url(self):
        pypi_url = self.cleaned_data.get("pypi_url")
        if (
            pypi_url
            and not pypi_url.startswith("http://")
            and not pypi_url.startswith("https://")
        ):
            pypi_url = f"https://pypi.org/project/{pypi_url}/"
        return pypi_url


class PackageCreateForm(BasePackageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["repo_url"].widget.attrs.update(
            {"readonly": True, "class": "text-muted-foreground bg-muted"}
        )


class PackageUpdateForm(BasePackageForm):
    pass


class FlaggedPackageForm(ModelForm):
    class Meta:
        model = FlaggedPackage
        fields = ["reason"]


class PackageExampleForm(ModelForm):
    class Meta:
        model = PackageExample
        fields = ["title", "url"]


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
