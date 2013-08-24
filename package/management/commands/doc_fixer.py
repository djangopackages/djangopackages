from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

import requests

from package.models import Package


class Command(NoArgsCommand):

    help = "Updates all the packages in the system by checking against their PyPI data."

    def handle(self, *args, **options):

        count = 0
        for package in Package.objects.exclude(documentation_url__in=("", None)):
            url = "https://readthedocs.org/projects/{}/".format(package.slug)
            r = requests.get(url)
            if r.status_code == 200:
                package.documentation_url = url
                package.save()
            count += 1
            print count, r.status_code, package.slug

