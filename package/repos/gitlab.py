from datetime import datetime
from django.conf import settings
from django.utils import timezone
from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError

from .base_handler import BaseHandler, RepoRateLimitError


class GitLabHandler(BaseHandler):
    title = "GitLab"
    url_regex = "(http|https|git)://gitlab.com/"
    url = "https://gitlab.com"
    repo_regex = r"(?:http|https|git)://gitlab.com/[^/]*/([^/]*)"
    slug_regex = repo_regex
    gitlab: Gitlab

    def __init__(self):
        if settings.GITLAB_TOKEN:
            self.gitlab = Gitlab(self.url, private_token=settings.GITLAB_TOKEN)
        else:
            self.gitlab = Gitlab(self.url)

    def _get_repo(self, repo_url):
        path = repo_url.replace(f"{self.url}/", "")
        return self.gitlab.projects.get(path, license=True)

    def _fetch_commit_stats(self, package, repo):
        # Fetch the most recent commit
        commits = repo.commits.list(per_page=1)
        if commits:
            last_commit = commits[0]
            package.last_commit_date = datetime.fromisoformat(
                last_commit.committed_date.replace("Z", "+00:00")
            )

        # Get total commit count from the default branch sequence endpoint
        # Use gitlab http_get to utilize session/auth
        path = f"/projects/{repo.id}/repository/commits/{repo.default_branch}/sequence"
        project_data = self.gitlab.http_get(path)

        package.commit_count = project_data["count"]

        # Build a 52-week histogram by fetching commits from the past year (or since last fetch)
        since_date, is_incremental = self._get_commits_update_params(package)
        since_str = since_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Paginate through all results
        all_commits = repo.commits.list(since=since_str, iterator=True)

        commit_dates = []
        for commit in all_commits:
            commit_dates.append(
                datetime.fromisoformat(commit.committed_date.replace("Z", "+00:00"))
            )

        self._process_commit_counts(package, commit_dates, is_incremental)

    def fetch_metadata(self, package, *, save: bool = True):
        try:
            repo = self._get_repo(package.repo_url)

            if repo is None:
                return package

            if hasattr(repo, "archived") and repo.archived:
                if not package.date_repo_archived:
                    package.date_repo_archived = timezone.now()

            package.repo_description = repo.description or ""
            package.repo_forks = repo.forks_count
            package.repo_watchers = repo.star_count

            contributors = [c["name"] for c in repo.repository_contributors()]

            if contributors:
                package.participants = ",".join(contributors)

            self._fetch_commit_stats(package, repo)

            if save:
                package.save()

            return package

        except GitlabGetError as exc:
            if getattr(exc, "response_code", None) == 429:
                raise RepoRateLimitError("gitlab rate limit reached")
            raise


repo_handler = GitLabHandler()
