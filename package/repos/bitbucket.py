import re
from warnings import warn

import requests

from .base_handler import BaseHandler

API_TARGET = "https://api.bitbucket.org/2.0/repositories"

descendants_re = re.compile(r"Forks/Queues \((?P<descendants>\d+)\)", re.IGNORECASE)


class BitbucketHandler(BaseHandler):
    title = "Bitbucket"
    url_regex = "https://bitbucket.org/"
    url = "https://bitbucket.org"
    repo_regex = r"https://bitbucket.org/[\w\-\_]+/([\w\-\_]+)/{0,1}"
    slug_regex = r"https://bitbucket.org/[\w\-\_]+/([\w\-\_]+)/{0,1}"

    def _get_bitbucket_commits(self, package):
        repo_name = package.repo_name()
        if repo_name.endswith("/"):
            repo_name = repo_name[:-1]
        # not sure if the limit parameter does anything in api 2.0
        target = f"{API_TARGET}/{repo_name}/commits/?limit=50"
        try:
            data = self.get_json(target)
        except requests.exceptions.HTTPError:
            return []
        if data is None:
            return []  # todo: log this?

        return data.get("values", [])

    def fetch_commits(self, package):
        from package.models import (
            Commit,
        )  # Import placed here to avoid circular dependencies

        for commit in self._get_bitbucket_commits(package):
            timestamp = commit["date"].split("+")
            if len(timestamp) > 1:
                timestamp = timestamp[0]
            else:
                timestamp = commit["date"]

            commit, _ = Commit.objects.get_or_create(
                package=package, commit_date=timestamp
            )

        self.refresh_commit_stats(package)

    def fetch_metadata(self, package):
        # prep the target name
        repo_name = package.repo_name()
        target = f"{API_TARGET}/{repo_name}"
        if not target.endswith("/"):
            target += "/"

        try:
            data = self.get_json(target)
        except requests.exceptions.HTTPError:
            return package

        if data is None:
            # TODO - log this better
            message = "%s had a JSONDecodeError during bitbucket.repo.pull" % (
                package.title
            )
            warn(message)
            return package

        # description
        package.repo_description = data.get("description", "")

        # get the forks of a repo
        url = f"{target}forks/"
        try:
            data = self.get_json(url)
        except requests.exceptions.HTTPError:
            return package
        package.repo_forks = len(data["values"])

        # get the followers of a repo
        url = f"{target}watchers/"
        try:
            data = self.get_json(url)
        except requests.exceptions.HTTPError:
            return package
        package.repo_watchers = len(data.get("values", []))

        # Getting participants
        try:
            package.participants = package.repo_url.split("/")[
                3
            ]  # the only way known to fetch this from bitbucket!!!
        except IndexError:
            package.participants = ""

        return package


repo_handler = BitbucketHandler()
