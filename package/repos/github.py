from time import sleep

from django.conf import settings
from django.utils import timezone

from github3 import GitHub, login
import requests

from base_handler import BaseHandler
from package.utils import uniquer


class GitHubHandler(BaseHandler):
    title = "Github"
    url_regex = '(http|https|git)://github.com/'
    url = 'https://github.com'
    repo_regex = r'(?:http|https|git)://github.com/[^/]*/([^/]*)/{0,1}'
    slug_regex = repo_regex

    def __init__(self):
        if settings.GITHUB_USERNAME:
            self.github = login(token=settings.GITHUB_TOKEN)
        else:
            self.github = GitHub()

    def manage_ratelimit(self):
        while self.github.ratelimit_remaining < 10:
            sleep(1)

    def fetch_metadata(self, package):
        self.manage_ratelimit()

        repo_name = package.repo_name()
        if repo_name.endswith("/"):
            repo_name = repo_name[:-1]
        try:
            username, repo_name = package.repo_name().split('/')
        except ValueError:
            return package
        repo = self.github.repository(username, repo_name)
        if repo is None:
            return package

        package.repo_watchers = repo.watchers
        package.repo_forks = repo.forks
        package.repo_description = repo.description

        contributors = [x.login for x in repo.iter_contributors()]
        if contributors:
            package.participants = ','.join(uniquer(contributors))

        return package

    def fetch_commits(self, package):

        self.manage_ratelimit()
        repo_name = package.repo_name()
        if repo_name.endswith("/"):
            repo_name = repo_name[:-1]
        try:
            username, repo_name = package.repo_name().split('/')
        except ValueError:
            # TODO error #248
            return package

        if settings.GITHUB_USERNAME:
            r = requests.get(
                url='https://api.github.com/repos/{}/{}/commits?per_page=100'.format(username, repo_name),
                auth=(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
            )
        else:
            r = requests.get(
                url='https://api.github.com/repos/{}/{}/commits?per_page=100'.format(username, repo_name)
            )
        if r.status_code == 200:
            from package.models import Commit  # Added here to avoid circular imports
            for commit in [x['commit'] for x in r.json()]:
                try:
                    commit, created = Commit.objects.get_or_create(
                        package=package,
                        commit_date=commit['committer']['date']
                    )
                except Commit.MultipleObjectsReturned:
                    pass

        package.save()
        return package

repo_handler = GitHubHandler()
