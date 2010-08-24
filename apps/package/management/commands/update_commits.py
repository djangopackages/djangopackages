import json
from string import ascii_lowercase
from sys import stdout
import threading

from django.core.management.base import BaseCommand, CommandError, NoArgsCommand
from django.db.models import Q

from github2.client import Github

from package.models import Package, Commit

class Command(BaseCommand):

    args = '<ascii_letter ascii_letter ...>'

    help = 'Updates all the packages in the system. Commands belongs to django-packages.apps.package'

    def handle(self, *args, **options):

        github = Github()

        count = 0
        threads = []
        for letter in args:
            letter = letter.lower()
            if letter == 'd':
                packages = Package.objects.filter(title__istartswith=letter).exclude(title__istartswith='django-').exclude(title__istartswith='django ')
            else:
                django_dash = 'django-%s' % letter
                django_space = 'django %s' % letter                
                packages = Package.objects.filter(
                            Q(title__istartswith=letter) | 
                            Q(title__istartswith=django_dash) |
                            Q(title__istartswith=django_space))            

            if packages.count():
                print >> stdout, '\nUpdating packages starting with the letter "%s"' % letter   
                for package in packages.filter(repo__title__icontains="github"):
                    try:
                        # add the commit history
                        for commit in github.commits.list(package.repo_name(), "master"):
                            commit, created = Commit.objects.get_or_create(package=package, commit_date=commit.committed_date)
                       
                        count += 1
                    except RuntimeError:
                        raise CommandError('Too many requests issued to Github threw a RuntimeError')
                    print >> stdout, '---Successfully updated package "%s"' % package.title

        print >> stdout, '\n%s packages updated' % count