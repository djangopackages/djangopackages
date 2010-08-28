import json
from sys import stdout
from time import sleep
from urllib import urlopen

from django.core.management.base import CommandError, NoArgsCommand

from github2.client import Github

from package.models import Package, Repo, Commit




class Command(NoArgsCommand):
    
    help = "Updates all the packages in the system. Commands belongs to django-packages.apps.package"    
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing package updating now"        
        
        # set up various useful bits
        github_repo = Repo.objects.get(title__icontains="github")
        bitbucket_repo = Repo.objects.get(title__icontains="bitbucket")    
        
        # instantiate the github connection
        github = Github()

        for index, package in enumerate(Package.objects.all()):
            zzz = 5

            
            try:
                if package.repo == github_repo:
                    # Do github
                    package.save()
                    for commit in github.commits.list(package.repo_name(), "master"):
                        commit, created = Commit.objects.get_or_create(package=package, commit_date=commit.committed_date)
                    zzz += 1
                elif package.repo == bitbucket_repo:
                    # do bitbucket
                    package.save()                    
                    for commit in get_bitbucket_commits(package):
                        commit, created = Commit.objects.get_or_create(package=package, commit_date=commit["timestamp"])
                else:
                    # unsupported so we skip and go on
                    print >> stdout, "%s. Skipped package '%s' because it uses an unsupported repo" % (index+1,package.title)
                    continue
            except RuntimeError, e:
                message = "For '%s', too many requests issued to repo threw a RuntimeError: %s" % (package.title, e)
                raise CommandError(message)
            sleep(zzz)
            print >> stdout, "%s. Successfully updated package '%s'" % (index+1,package.title)

        print >> stdout, "-" * 40

def get_bitbucket_commits(package):
    repo_name = package.repo_name()
    if repo_name.endswith("/"):
        repo_name = repo_name[0:-1]
    target = "http://api.bitbucket.org/1.0/repositories/%s/changesets/?limit=50" % repo_name
    page = urlopen(target).read()
    try:
        data = json.loads(page)
    except ValueError, e:
        # TODO - fix this problem with bad imports from bitbucket
        print >> stdout, "Problems with %s" % package.title
        print >> stdout, target        
        print >> stdout, e
        data = {}
    return data.get("changesets", [])
    
    