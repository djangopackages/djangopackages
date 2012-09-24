""" 
Base class for objects that interact with third-party code repository services.
"""

import json

import requests


class BaseHandler(object):

    def __str__(self):
        return self.title

    @property
    def title(self):
        """ title for display in drop downs:

                return: string
                example: 'Github'
        """
        return NotImplemented

    @property
    def url(self):
        """ base value for url API interation:

                return: URL string
                example: 'https://github.com'
        """
        return NotImplemented

    def fetch_metadata(self, package):
        """ Accepts a package.models.Package instance:

                return: package.models.Package instance

            Must set the following fields:

                package.repo_watchers (int)
                package.repo_forks (int)
                package.repo_description (text )
                package.participants = (comma-seperated value)

        """
        return NotImplemented

    def fetch_commits(self, package):
        """ Accepts a package.models.Package instance:
        """
        return NotImplemented

    @property
    def is_other(self):
        """ DON'T CHANGE THIS PROPERTY! This should only be overridden by
        the unsupported handler.

                return: False
        """
        return False

    @property
    def user_url(self):
        """ identifies the user URL:

                example:
        """
        return ''

    @property
    def repo_regex(self):
        """ Used by the JavaScript forms """
        return NotImplemented

    @property
    def slug_regex(self):
        """ Used by the JavaScript forms """
        return NotImplemented

    def packages_for_profile(self, profile):
        """ Return a list of all packages contributed to by a profile. """
        repo_url = profile.url_for_repo(self)
        if repo_url:
            from package.models import Package
            regex = r'^{0},|,{0},|{0}$'.format(repo_url)
            return list(Package.objects.filter(participants__regex=regex, repo_url__regex=self.repo_regex))
        else:
            return []

    def serialize(self):
        return {
            "title": self.title,
            "url": self.url,
            "repo_regex": self.repo_regex,
        }

    def get_json(self, target):
        """
        Helpful utility method to do a quick GET for JSON data.
        """
        r = requests.get(target)
        if r.status_code != 200:
            r.raise_for_status()
        return json.loads(r.content)
