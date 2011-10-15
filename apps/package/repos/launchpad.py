import datetime
import json
import os

import requests
from bzrlib.branch import Branch
from launchpadlib.launchpad import Launchpad

from django.conf import settings

from .base_handler import BaseHandler

LAUNCHPAD_URL = 'https://api.launchpad.net/1.0/'

class LaunchpadAPIError(Exception):
    pass


class LaunchpadHandler(BaseHandler):
    title = 'Launchpad'
    url_regex = 'https://code.launchpad.net/'
    url = 'https://code.launchpad.net'
    user_url = 'https://launchpad.net/~%s'
    repo_regex = r'https://code.launchpad.net/~[\w\-\_]+/([\w\-\_]+)/[\w\-\_]+/{0,1}'
    slug_regex = r'https://code.launchpad.net/~[\w\-\_]+/([\w\-\_]+)/[\w\-\_]+/{0,1}'

    def fetch_commits(self, package):
        from package.models import Commit # Import placed here to avoid circular dependencies
        """
        repo_name = package.repo_name()
        branch_url = '%s%s' % (LAUNCHPAD_URL, repo_name)
        print branch_url
        branch = requests.get(branch_url)
        if branch.status_code == 200:
            data = json.loads(branch.content)
            keys = data.keys()
            keys.sort()
            print keys
            for k,v in data.items():
                print k
                print v
                print '-'*20                
            #entries = data[u'entries']
            #print entries[0]
            #print entries[1]      
            #print entries[2]
            #for revision in data[u'entries']:
            #    print revision
            #    timestamp =  datetime.datetime.fromtimestamp(revision.timestamp)
            #    break
            
        else:
            msg = "{0} failed with a {1} HTTP status code".format(repo_name, branch.status_code)
            raise LaunchpadAPIError(msg)
        """            
        
        branch = Branch.open(package.repo_url)
        repository = branch.repository
        for revision_id in branch.revision_history():
            revision = repository.get_revision(revision_id)
            timestamp = datetime.datetime.fromtimestamp(revision.timestamp)
            commit, created = Commit.objects.get_or_create(package=package, commit_date=timestamp)

    def fetch_metadata(self, package):
        #cachedir = getattr(settings, 'LAUNCHPAD_CACHE_DIR', os.path.join(settings.PROJECT_ROOT, 'lp-cache'))
        #launchpad = Launchpad.login_anonymously('djangopackages.com', 'production', cachedir)
        repo_name = package.repo_name()
        #print repo_name

        #branch = launchpad.branches.getByUrl(url='lp:%s' % repo_name)

        #package.repo_description = branch.description or ''
        #package.repo_forks = len(branch.project.getBranches())
        #package.repo_watchers = len(branch.subscribers)
        #package.participants = branch.owner.name

        return package

repo_handler = LaunchpadHandler()

