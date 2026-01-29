import re
from datetime import datetime
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

    def _fetch_commit_stats(self, package, repo):
        # Fetch the most recent commit to get the last commit date
        # and use the Link header to get the total commit count
        commits = repo.commits(per_page=1)
        last_commit = next(commits, None)

        if last_commit:
            package.last_commit_date = datetime.fromisoformat(
                last_commit.commit.committer["date"].replace("Z", "+00:00")
            )

        # Parse the Link header to determine total commit count
        total_commits = 0
        if commits.last_response:
            link_header = commits.last_response.headers.get("Link")
            if link_header and 'rel="last"' in link_header:
                match = re.search(r"page=(\d+)>; rel=\"last\"", link_header)
                if match:
                    total_commits = int(match.group(1))
        package.commit_count = total_commits

        # Fetch weekly participation statistics
        # GitHub provides a pre-computed 52-week histogram
        stats = repo.weekly_commit_count()
        if stats and "all" in stats:
            package.commits_over_52w = stats["all"]

    def fetch_metadata(self, package, *, save: bool = True):
        self.manage_ratelimit()

        try:
            repo = self._get_repo(package)
            if repo is None:
                return package

            if repo.archived:
                if not package.date_repo_archived:
                    package.date_repo_archived = timezone.now()

            package.repo_description = repo.description or ""
            package.repo_forks = repo.forks_count
            package.repo_watchers = repo.watchers_count

            contributors = []
            for contributor in repo.contributors():
                contributors.append(contributor.login)
                self.manage_ratelimit()

            if contributors:
                package.participants = ",".join(uniquer(contributors))

            self._fetch_commit_stats(package, repo)

            if save:
                package.save()

            return package

        except NotFoundError:
            raise

    def manage_ratelimit(self):
        if self.github.ratelimit_remaining and self.github.ratelimit_remaining < 10:
            raise RepoRateLimitError("github rate limit reached")


repo_handler = GitHubHandler()
