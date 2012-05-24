"""
    Original Source: https://github.com/jacobian/django-dev-dashboard/blob/master/dashboard/middleware.py
    Permission: Granted by Jacob Kaplan-Moss on 5/23/2012
    License: https://github.com/jacobian/django-dev-dashboard/blob/master/LICENSE.txt
"""

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.http import urlquote
from django.shortcuts import redirect

class CanonicalDomainMiddleware(object):
    """
    Force-redirect to settings.CANONICAL_HOSTNAME if that's not the domain
    being accessed. If the setting isn't set, do nothing.
    """
    def __init__(self):
        try:
            self.canonical_hostname = settings.CANONICAL_HOSTNAME
        except AttributeError:
            raise MiddlewareNotUsed("settings.CANONICAL_HOSTNAME is undefined")

    def process_request(self, request):
        if request.get_host() == self.canonical_hostname:
            return

        # Domains didn't match, so do some fixups.
        new_url = [
            'https' if request.is_secure() else 'http',
            '://',
            self.canonical_hostname,
            urlquote(request.path),
            '?%s' % request.GET.urlencode() if request.GET else ''
        ]
        return redirect(''.join(new_url), permanent=True)