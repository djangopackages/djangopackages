from time import sleep

from django.conf import settings
from django.utils import timezone

from github3 import GitHub, login
import requests

from .base_handler import BaseHandler
from package.utils import uniquer


class GitHubHandler(BaseHandler):
    title = "Github"
    url_regex = '(http|https|git)://github.com/'
    url = 'https://github.com'
    repo_regex = r'(?:http|https|git)://github.com/[^/]*/([^/]*)/{0,1}'
    slug_regex = repo_regex

    def __init__(self):
        if settings.GITHUB_TOKEN:
            self.github = login(token=settings.GITHUB_TOKEN)
        else:
            self.github = GitHub()

    def manage_ratelimit(self):
        while self.github.ratelimit_remaining < 10:
            sleep(1)

    def _get_repo(self, package):
        repo_name = package.repo_name()
        if repo_name.endswith("/"):
            repo_name = repo_name[:-1]
        try:
            username, repo_name = package.repo_name().split('/')
        except ValueError:
            return None
        return self.github.repository(username, repo_name)


    def fetch_metadata(self, package):
        self.manage_ratelimit()
        repo = self._get_repo(package)
        if repo is None:
            return package

        package.repo_watchers = repo.watchers
        package.repo_forks = repo.forks
        package.repo_description = repo.description

        contributors = []
        for contributor in repo.iter_contributors():
            contributors.append(contributor.login)
            self.manage_ratelimit()

        if contributors:
            package.participants = ','.join(uniquer(contributors))

        return package

    def fetch_commits(self, package):

        self.manage_ratelimit()
        repo = self._get_repo(package)
        if repo is None:
            return package

        from package.models import Commit  # Added here to avoid circular imports

        for commit in repo.iter_commits():
            self.manage_ratelimit()
            try:
                commit_record, created = Commit.objects.get_or_create(
                    package=package,
                    commit_date=commit.commit.committer['date']
                )
                if not created:
                    break
            except Commit.MultipleObjectsReturned:
                continue
            # If the commit record already exists, it means we are at the end of the
            #   list we want to import

        package.save()
        return package

repo_handler = GitHubHandler()
