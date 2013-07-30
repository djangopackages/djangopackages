from time import sleep

from django.conf import settings

from github3 import GitHub, login

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
            self.github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
        else:
            print "TEEESSSST"
            self.github = GitHub()

    def manage_ratelimit(self):
        while self.github.ratelimit_remaining < 10:
            sleep(1)

    def fetch_metadata(self, package):
        self.manage_ratelimit()

        username, repo_name = package.repo_name().split('/')
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
        username, repo_name = package.repo_name().split('/')
        repo = self.github.repository(username, repo_name)
        if repo is None:
            return package
        package.commit_list = str([x['total'] for x in repo.iter_commit_activity(number=52)])
        if package.commit_list.strip() == '[]':
            return package
        package.save()
        return package

repo_handler = GitHubHandler()
