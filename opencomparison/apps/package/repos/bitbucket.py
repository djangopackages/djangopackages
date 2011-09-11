import re
from urllib import urlopen
from warnings import warn

try:
    import simplejson as json
except ImportError:
    import json

from .base_handler import BaseHandler

API_TARGET = "https://api.bitbucket.org/1.0/repositories"

descendants_re = re.compile(r"Forks/Queues \((?P<descendants>\d+)\)", re.IGNORECASE)


class BitbucketHandler(BaseHandler):
    title = 'Bitbucket'
    url_regex = 'https://bitbucket.org/'
    url = 'https://bitbucket.org'
    repo_regex = r'https://bitbucket.org/[\w\-\_]+/([\w\-\_]+)/{0,1}'
    slug_regex = r'https://bitbucket.org/[\w\-\_]+/([\w\-\_]+)/{0,1}'

    def _get_bitbucket_commits(self, package):
        repo_name = package.repo_name()
        if repo_name.endswith("/"):
            repo_name = repo_name[0:-1]
        target = "%s/%s/changesets/?limit=50" % (API_TARGET, repo_name)
        page = urlopen(target).read()
        try:
            data = json.loads(page)
        except ValueError, e:
            # TODO - fix this problem with bad imports from bitbucket
            data = {}
        return data.get("changesets", [])

    def fetch_commits(self, package):
        from package.models import Commit # Import placed here to avoid circular dependencies
        for commit in self._get_bitbucket_commits(package):
            timestamp = commit["timestamp"].split("+")
            if len(timestamp) > 1:
                timestamp = timestamp[0]
            else:
                timestamp = commit["timestamp"]
            commit, created = Commit.objects.get_or_create(package=package, commit_date=timestamp)

    def fetch_metadata(self, package):
        # prep the target name
        repo_name = package.repo_name()
        target = API_TARGET + "/" + repo_name
        if not target.endswith("/"):
            target += "/"
        
        # open the target and read the content
        response = urlopen(target)
        response = response.read()
        
        # dejsonify the results
        try:
            data = json.loads(response)
        except json.decoder.JSONDecodeError:
            # TODO - log this better
            message = "%s had a JSONDecodeError during bitbucket.repo.pull" % (package.title)
            warn(message)
            return package

        # description
        package.repo_description = data.get("description","")
        
        # screen scrape to get the repo_forks off of bitbucket HTML pages
        descendants_target = package.repo_url
        if not descendants_target.endswith("/"):
            descendants_target += "/"
        descendants_target += "descendants"
        html = urlopen(descendants_target)
        html = html.read()
        try:
            package.repo_forks = descendants_re.search(html).group("descendants")
        except AttributeError:
            package.repo_forks = 0
                    
        # get the followers of a repo
        # get the followers of a repo
        # get the followers of a repo                
        url = "{0}followers/".format(target)
        page = urlopen(url).read()
        data = json.loads(page)
        package.repo_watchers = data['count']      
        
        # Getting participants
        try:
            package.participants = package.repo_url.split("/")[3] # the only way known to fetch this from bitbucket!!!
        except IndexError:
            package.participants = ""          
            
        return package

repo_handler = BitbucketHandler()
