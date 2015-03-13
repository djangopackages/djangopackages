from django.conf.urls import patterns, url
from django.views.generic import RedirectView

class APIRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Return the URL redirect to. Keyword arguments from the
        URL pattern match generating the redirect request
        are provided as kwargs to this method.
        """
        chunk = kwargs['chunk']

        bits = chunk.split('/')

        # Category listings
        if chunk.startswith('category'):
            url = chunk.replace('category', '/api/v3/categories/')
        # Grid Packages
        elif len(bits) == 3 and bits[0] == 'grid' and bits[2] == 'packages':
            url = '/api/v3/grids/{0}/packages'.format(bits[1])
        # Grids
        elif chunk.startswith('grid'):
            url = chunk.replace('grid', '/api/v3/grids/')
        elif chunk.startswith('user'):
            url = chunk.replace('user', '/api/v3/users/')
        elif chunk.startswith('package'):
            url = chunk.replace('package', '/api/v3/packages/')
        else:
            return None

        url = url.replace('//', '/')

        # Add in the arguments
        args = self.request.META.get('QUERY_STRING', '')
        url = "%s?%s" % (url, args)
        return url

urlpatterns = patterns("",
    url(
        regex=r"^(?P<chunk>[-\w\/]+)/$",
        view=APIRedirectView.as_view(),
        name="api_redirect",
    )
)