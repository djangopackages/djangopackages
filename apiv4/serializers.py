import six

from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch

from rest_framework import relations
from rest_framework.reverse import reverse
from rest_framework import serializers

from grid.models import Grid
from package.models import Package, Category
from searchv2.models import SearchV2

class GridSerializer(serializers.ModelSerializer):
    packages = serializers.HyperlinkedRelatedField(many=True, view_name='apiv4:package-detail', read_only=True)

    class Meta:
        model = Grid

class PackageSerializer(serializers.HyperlinkedModelSerializer):
    # 'Source' is attached to the model attribute
    participants = serializers.ListField(source='participant_list')
    commits_over_52 = serializers.ListField(source='commits_over_52_listed')
    grids = serializers.HyperlinkedRelatedField(many=True, view_name='apiv4:grid-detail', read_only=True)
    category = serializers.HyperlinkedRelatedField(view_name='apiv4:category-detail', read_only=True)

    class Meta:
        model = Package
        fields = (
            'category',
            'grids',
            'id',
            'title',
            'slug',
            'last_updated',
            'last_fetched',
            'repo_url',
            'pypi_version',
            'created',
            'modified',
            'repo_forks',
            'repo_description',
            'pypi_url',
            'documentation_url',
            'repo_watchers',
            'commits_over_52',
            'participants',
        )

class SearchV2Hyperlink(serializers.HyperlinkedRelatedField):

    view_name = 'package-detail'

    def get_url(self, obj, view_name, request, format):
        import ipdb; ipdb.set_trace()
        url_kwargs = {
            'organization_slug': obj.organization.slug,
            'customer_pk': obj.pk
        }
        return reverse(view_name, url_kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        import ipdb; ipdb.set_trace()
        lookup_kwargs = {
           'organization__slug': view_kwargs['organization_slug'],
           'pk': view_kwargs['customer_pk']
        }
        return self.get_queryset().get(**lookup_kwargs)

class HyperlinkFeld(serializers.HyperlinkedRelatedField):

    lookup_field = 'pk'

    def get_url(self, obj, view_name):
        """
        Given an object, return the URL that hyperlinks to the object.
        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk is None:
            return None
        kwargs = {'pk': 1}
        return reverse(view_name, kwargs=kwargs)

    def to_representation(self, value):

        self.view_name = "apiv4:{}-detail".format(value.item_type)


        try:
            url = self.get_url(value, self.view_name)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            if value in ('', None):
                value_string = {'': 'the empty string', None: 'None'}[value]
                msg += (
                    " WARNING: The value of the field on the model instance "
                    "was %s, which may be why it didn't match any "
                    "entries in your URL conf." % value_string
                )
            raise ImproperlyConfigured(msg % self.view_name)

        if url is None:
            return None

        return relations.Hyperlink(url, six.text_type(value))


class SearchV2Serializer(serializers.ModelSerializer):

    # resource_uri = HyperlinkFeld(source='_self')

    class Meta:
        model = SearchV2
        exclude = ['id', ]


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
