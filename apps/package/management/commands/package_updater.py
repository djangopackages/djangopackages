from sys import stdout
from time import sleep

from django.core.management.base import CommandError, NoArgsCommand

from github2.client import Github

from package.models import Package, Commit


class Command(NoArgsCommand):
    
    help = "Updates all the packages in the system. Commands belongs to django-packages.apps.package"
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing package updating now"
        
        github = Github()

        for index, package in enumerate(Package.objects.all()):
            zzz = 5
            try:
                package.save()
                if "github" in package.repo.title.lower():
                    for commit in github.commits.list(package.repo_name(), "master"):
                        commit, created = Commit.objects.get_or_create(package=package, commit_date=commit.committed_date)                
                    zzz += 1
            except RuntimeError, e:
                message = "For '%s', too many requests issued to repo threw a RuntimeError: %s" % (package.title, e)
                raise CommandError(message)
            sleep(zzz)
            print >> stdout, "%s. Successfully updated package '%s'" % (index+1,package.title)

        print >> stdout, "-" * 40
        print >> stdout, "%s packages updated" % index +1
    
                
