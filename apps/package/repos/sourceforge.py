import re
from urllib import urlopen

try:
    import simplejson as json
except ImportError:
    import json

from .base_handler import BaseHandler

API_TARGET = "https://sourceforge.net/api"

class SourceforgeError(Exception):
    """An error occurred when making a request to the Sourceforge API"""

class SourceforgeHandler(BaseHandler):
    """
    The Sourceforge API has some tricky stuff in it - some sections are fed
    via xml/rss, some are via json. As of 03/16/2011, the xml API is the most
    up-to-date, but a bug has been opened to fix the json side. This API is
    on hold until it is fixed.
    """

    title = "Sourceforge"
    url = "https://sourceforge.net"
    repo_regex = r'https://sourceforge.com/[\w\-\_]+/([\w\-\_]+)/{0,1}'
    slug_regex = r'https://sourceforge.com/[\w\-\_]+/([\w\-\_]+)/{0,1}'

    def fetch_metadata(self, package):
        sourceforge = '';

        repo_name = package.repo_name()
        target = API_TARGET + "/projects/name/" + repo_name
        if not target.endswith("/"):
            target += "/"

        # sourceforge project API requires ending with /doap/
        target += "json/"

        # open the target and read the content
        response = urlopen(target)
        response_text = response.read()

        # dejson the results
        try:
            data = json.loads(response_text)
        except jason.decoder.JSONDecodeError:
            raise SourceforgeError("unexpected response from sourceforge.net %d: %r" % (
                                   response.status, response_text))

        # sourceforge has both developers and maintainers in a list
        participants = data.get("developers").append(data.get("maintainers"))
        package.participants = [p['name'] for p in participants]

        package.repo_description = data.get("description")

        project_name = _name_from_pypi_home_page(package.pypi_home_page)
        # dejsonify the results
        try:
            sf_package_data = _get_project_data(project_name)
        except json.decoder.JSONDecodeError:
            message = "%s had a JSONDecodeError while loading %s" % (package.title,
                                                                     package_json_path)
            warn(message)
            return package
        package.repo_watchers = len(sf_package_data.get('maintainers', [])) + len(sf_package_data.get('developers', [])) 
        package.repo_description = sf_package_data.get('description', '')
        # TODO - remove the line below and use repo_url as your foundation    
        package.repo_url = _get_repo_url(sf_package_data)
        package.repo_forks = None

        return package

repo_handler = SourceforgeHandler()
