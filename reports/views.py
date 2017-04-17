# -*- coding: utf-8 -*-


import csv
import io

from django.http import HttpResponse

from package.models import Package



def package_csv(request):

    output = io.StringIO()
    fieldnames = ['title', 'created', 'num_participants', 'pypi_downloads', 'repo_forks', ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    for package in Package.objects.all():
        try:
            writer.writerow(
                {
                    'title': package.title,
                    'created': package.created,
                    'num_participants': len(package.participants.split(',')),
                    'pypi_downloads': 'TODO', # This doesn't work: package.pypi_downloads,
                    'repo_forks': package.repo_forks

                }
            )
        except UnicodeEncodeError:
            pass

    result = ','.join(fieldnames)
    result += '\n'
    result += output.getvalue()


    return HttpResponse(result)
