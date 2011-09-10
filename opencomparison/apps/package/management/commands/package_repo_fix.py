from sys import stdout
from time import strftime, gmtime

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from package.models import Package, Repo

date_string = "%a, %d %b %Y %H:%M:%S +0000"

class Command(NoArgsCommand):
    
    help = "Corrects bitbucket and github accounts to their correct prefix and repo"    
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing repo fix at %s " % strftime(date_string, gmtime())
        
        
        # set up various useful bits
        github_repo = Repo.objects.get(title__icontains="github")
        bitbucket_repo = Repo.objects.get(title__icontains="bitbucket")    
        fixes = 0
        
        for index, package in enumerate(Package.objects.all()):
    
            repo_url = package.repo_url
            
            if 'github' not in repo_url and 'bitbucket' not in repo_url:
                continue

            if repo_url.startswith('https://github') or repo_url.startswith('http://github'): 
                package.repo_url = repo_url.replace('http://github','https://github')
                package.repo = github_repo

            if repo_url.startswith('https://bitbucket') or repo_url.startswith('http://bitbucket'): 
                package.repo_url = repo_url.replace('http://bitbucket','https://bitbucket')
                package.repo = bitbucket_repo

            package.save()
            print >> stdout, "%s. Successfully corrected package '%s'" % (index+1,package.title)
            fixes += 1

        print >> stdout, "-" * 40
        print >> stdout, "Finished at %s" % strftime(date_string, gmtime())

    
