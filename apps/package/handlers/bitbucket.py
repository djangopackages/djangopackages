import re
from urllib import urlopen
from warnings import warn

try:
    import simplejson as json
except ImportError:
    import json

from package.utils import uniquer

API_TARGET = "http://api.bitbucket.org/1.0/repositories/"

descendants_re = re.compile(r"Forks/Queues \((?P<descendants>\d+)\)")


def pull(package):
    
    # prep the target name
    repo_name = package.repo_name()
    target = API_TARGET + repo_name
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

    package.repo_watchers    = data.get("followers_count",0)
    package.repo_description = data.get("description","")
    
    # screen scrape to get the repo_forks off of bitbucket HTML pages
    target = package.repo_url
    if not target.endswith("/"):
        target += "/"
    target += "descendants"
    html = urlopen(target)
    html = html.read()
    package.repo_forks = descendants_re.search(html).group("descendants")
    
    try:
        package.participants = package.repo_url.split("/")[3] # the only way known to fetch this from bitbucket!!!
    except IndexError:
        package.participants = ""
        
    return package
