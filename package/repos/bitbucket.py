from datetime import datetime, timedelta
import re
from warnings import warn


from .base_handler import BaseHandler

import requests

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
        try:
            data = self.get_json(target)
        except requests.exceptions.HTTPError:
            return []
        if data is None:
            return []  # todo: log this?

        return data.get("changesets", [])

    def fetch_commits(self, package):
        from package.models import Commit  # Import placed here to avoid circular dependencies
        for commit in self._get_bitbucket_commits(package):
            timestamp = commit["timestamp"].split("+")
            if len(timestamp) > 1:
                timestamp = timestamp[0]
            else:
                timestamp = commit["timestamp"]
            commit, created = Commit.objects.get_or_create(package=package, commit_date=timestamp)

        #  ugly way to get 52 weeks of commits
        # TODO - make this better
        now = datetime.now()
        commits = package.commit_set.filter(
            commit_date__gt=now - timedelta(weeks=52),
        ).values_list('commit_date', flat=True)

        weeks = [0] * 52
        for cdate in commits:
            age_weeks = (now - cdate).days // 7
            if age_weeks < 52:
                weeks[age_weeks] += 1

        package.commit_list = ','.join(map(str, reversed(weeks)))
        package.save()

    def fetch_metadata(self, package):
        # prep the target name
        repo_name = package.repo_name()
        target = API_TARGET + "/" + repo_name
        if not target.endswith("/"):
            target += "/"

        try:
            data = self.get_json(target)
        except requests.exceptions.HTTPError:
            return package

        if data is None:
            # TODO - log this better
            message = "%s had a JSONDecodeError during bitbucket.repo.pull" % (package.title)
            warn(message)
            return package

        # description
        package.repo_description = data.get("description", "")

        # get the forks of a repo
        url = "{0}forks/".format(target)
        try:
            data = self.get_json(url)
        except requests.exceptions.HTTPError:
            return package
        package.repo_forks = len(data['forks'])

        # get the followers of a repo
        url = "{0}followers/".format(target)
        try:
            data = self.get_json(url)
        except requests.exceptions.HTTPError:
            return package
        package.repo_watchers = data['count']

        # Getting participants
        try:
            package.participants = package.repo_url.split("/")[3]  # the only way known to fetch this from bitbucket!!!
        except IndexError:
            package.participants = ""

        return package

repo_handler = BitbucketHandler()
