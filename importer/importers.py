import json
import requests
import re

from django.db import IntegrityError
from django.db.models import Q # for 'OR' queries

from core.utils import oc_slugify, get_pypi_url
from package.models import Package, Category

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
        title = match.group('slug')
        slug = oc_slugify(title)

         # Need: title, slug, category, repo_url
         # Optional but recommended: pypi_url
        category = Category.objects.get(slug=category_slug)

        # Does the slug or repo already exist?
        packages = Package.objects.filter(Q(slug=slug) | Q(repo_url=html_url))

        if packages.count():
            continue

        package = Package.objects.create(title=title, slug=slug, category=category, repo_url=html_url)        
        pypi_url = get_pypi_url(title)
        if pypi_url:
            package.pypi_url = pypi_url
        package.save()            
        
        imported_packages.append(package)
        
    return imported_packages
