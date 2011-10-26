import json
import requests
import re

from django.db import IntegrityError
from django.db.models import Q # for 'OR' queries

from core.utils import oc_slugify
from package.models import Package, Category

from sys import stdout
def import_from_github_acct(github_name, user_type, category_slug):
    """ Imports all packages from a specified Github account """

    url = 'https://api.github.com/%ss/%s/repos' % (user_type, github_name)
    r = requests.get(url)

    imported_packages = []
    data = json.loads(r.content)
    for repo in data:
        html_url = repo[u'html_url']
        regex = r'https://github.com/' + github_name + r'/(?P<slug>[\w\-\.]+)'
        match = re.match(regex, html_url)
        slug = oc_slugify(match.group('slug'))

         # Need: title, slug, category, repo_url
         # Optional but recommended: pypi_url
        category = Category.objects.get(slug=category_slug)

        # Does the slug or repo already exist?
        packages = Package.objects.filter(Q(slug=slug) | Q(repo_url=html_url))

        if packages.count():
            continue
        else:
            try:
                package = Package.objects.create(title=slug, slug=slug, category=category, repo_url=html_url)
                package.save()
                imported_packages += slug
            except IntegrityError:
                print "Could not save package %s" % html_url
        
    return imported_packages
