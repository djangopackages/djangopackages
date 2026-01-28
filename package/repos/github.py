from django.conf import settings
from django.utils import timezone
from github3 import GitHub, login
from github3.exceptions import NotFoundError

from package.utils import uniquer

from .base_handler import BaseHandler, RepoRateLimitError


class GitHubHandler(BaseHandler):
    title = "GitHub"
    url_regex = "(http|https|git)://github.com/"
    url = "https://github.com"
    repo_regex = r"(?:http|https|git)://github.com/[^/]*/([^/]*)/{0,1}"
    slug_regex = repo_regex

    def __init__(self):
        if settings.GITHUB_TOKEN:
            self.github = login(token=settings.GITHUB_TOKEN)
        else:
            self.github = GitHub()

    def _get_repo(self, package):
        repo_name = package.repo_name()
        if repo_name.endswith("/"):
            repo_name = repo_name[:-1]
        try:
            username, repo_name = package.repo_name().split("/")
        except ValueError:
            return None
        return self.github.repository(username, repo_name)

    def fetch_commits(self, package, *, save: bool = True):
        self.manage_ratelimit()

        repo = self._get_repo(package)
        if repo is None:
            return package

        from package.models import Commit  # Added here to avoid circular imports

        for commit in repo.commits():
            self.manage_ratelimit()

            try:
                _, created = Commit.objects.get_or_create(
                    package=package, commit_date=commit.commit.committer["date"]
                )
                # If the commit record already exists, it means we are at the end of the
                # list we want to import
                if not created:
                    break
            except Commit.MultipleObjectsReturned:
                continue

        if save:
            package.save()

        return package

    def fetch_metadata(self, package, *, save: bool = True):
        self.manage_ratelimit()

        try:
            repo = self._get_repo(package)
            if repo is None:
                return package

            if repo.archived:
                if not package.date_repo_archived:
                    package.date_repo_archived = timezone.now()

            package.repo_description = repo.description
            package.repo_forks = repo.forks_count
            package.repo_watchers = repo.watchers_count
            # repo.stargazers_count

            contributors = []
            for contributor in repo.contributors():
                contributors.append(contributor.login)
                self.manage_ratelimit()

            if contributors:
                package.participants = ",".join(uniquer(contributors))

            if save:
                package.save()

            return package

        except NotFoundError:
            raise

    def manage_ratelimit(self):
        if self.github.ratelimit_remaining < 10:
            raise RepoRateLimitError("github rate limit reached")


repo_handler = GitHubHandler()
