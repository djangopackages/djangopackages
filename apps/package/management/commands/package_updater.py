import datetime
import json
from socket import error as socket_error
from sys import stdout
from time import sleep, gmtime, strftime
from urllib import urlopen

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from bzrlib.branch import Branch
from github2.client import Github

from package.models import Package, Repo, Commit

class Command(NoArgsCommand):
    
    help = "Updates all the packages in the system. Commands belongs to django-packages.apps.package"    
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing package updating now at %s " % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        
        # set up various useful bits
        github_repo = Repo.objects.get(title__icontains="github")
        bitbucket_repo = Repo.objects.get(title__icontains="bitbucket") 
        launchpad_repo = Repo.objects.get(title__icontains="launchpad")
        
        # instantiate the github connection
        if hasattr(settings, "GITHUB_ACCOUNT") and hasattr(settings, "GITHUB_KEY"):
            github   = Github(username=settings.GITHUB_ACCOUNT, api_token=settings.GITHUB_KEY)
            authed = True
        else:
            github   = Github()
            authed = False

        for index, package in enumerate(Package.objects.all()):
            zzz = 5
            
            try:
                if package.repo == github_repo:
                    # Do github
                    try:
                        package.fetch_metadata()
                    except socket_error, e:
                        print >> stdout, "For '%s', threw a socket.error: %s" % (package.title, e)
                        continue
                    for commit in github.commits.list(package.repo_name(), "master"):
                        commit, created = Commit.objects.get_or_create(package=package, commit_date=commit.committed_date)
                    zzz += 1
                elif package.repo == bitbucket_repo:
                    zzz = 1
                    # do bitbucket
                    try:
                        package.fetch_metadata()
                    except socket_error, e:
                        print >> stdout, "For '%s', threw a socket.error: %s" % (package.title, e)
                        continue                  
                    for commit in get_bitbucket_commits(package):
                        commit, created = Commit.objects.get_or_create(package=package, commit_date=commit["timestamp"])
                elif package.repo == launchpad_repo:
                    try:
                        branch = Branch.open(package.repo_url)
                        repository = branch.repository
                        for revision_id in branch.revision_history():
                            revision = repository.get_revision(revision_id)
                            timestamp = datetime.datetime.fromtimestamp(revision.timestamp)
                            commit, created = Commit.objects.get_or_create(package=package, commit_date=timestamp)
                    except Exception, e:
                        print >> stdout, "For '%s', threw an exception: %s" % (package.title, e)
                        continue
                else:
                    # unsupported so we just get metadata and go on
                    try:
                        package.fetch_metadata()
                    except socket_error, e:
                        print >> stdout, "For '%s', threw a socket.error: %s" % (package.title, e)
                        continue               
                    
            except RuntimeError, e:
                message = "For '%s', too many requests issued to repo threw a RuntimeError: %s" % (package.title, e)
                print >> stdout, message
                continue
            except UnicodeDecodeError, e:
                message = "For '%s', UnicodeDecodeError: %s" % (package.title, e)
                print >> stdout, message
                continue                
                
            if not authed:
               sleep(zzz)
            print >> stdout, "%s. Successfully updated package '%s'" % (index+1,package.title)

        print >> stdout, "-" * 40
        print >> stdout, "Finished at %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

def get_bitbucket_commits(package):
    repo_name = package.repo_name()
    if repo_name.endswith("/"):
        repo_name = repo_name[0:-1]
    target = "https://api.bitbucket.org/1.0/repositories/%s/changesets/?limit=50" % repo_name
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
    
    
