from floppyforms.__future__ import ModelForm, TextInput

from package.models import Category, Package, PackageExample


def package_help_text():
    help_text = ""
    for category in Category.objects.all():
        help_text += """<li><strong>{title_plural}</strong> {description}</li>""".format(
                        title_plural=category.title_plural,
                        description=category.description
                        )
    help_text = "<ul>{0}</ul>".format(help_text)
    return help_text


class PackageForm(ModelForm):

    def __init__(self, *args, **kwargs):
            super(PackageForm, self).__init__(*args, **kwargs)
            self.fields['category'].help_text = package_help_text()
            self.fields['repo_url'].required = True
            self.fields['repo_url'].widget = TextInput(attrs={
                'placeholder': 'ex: https://github.com/django/django'
            })

    def clean_slug(self):
        return self.cleaned_data['slug'].lower()

    class Meta:
        model = Package
        fields = ['repo_url', 'title', 'slug', 'pypi_url', 'category', ]


class PackageExampleForm(ModelForm):

    class Meta:
        model = PackageExample
        fields = ['title', 'url']


class PackageExampleModeratorForm(ModelForm):

    class Meta:
        model = PackageExample
        fields = ['title', 'url', 'active']


class DocumentationForm(ModelForm):

    class Meta:
        model = Package
        fields = ["documentation_url", ]
