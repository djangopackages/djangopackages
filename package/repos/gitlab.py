from datetime import datetime
from urllib.parse import urlparse

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

    def __init__(self):
        self.client = None
        self._client_cache: dict[str, Gitlab] = {}

    def get_base_url(self, repo_url: str) -> str:
        """The instance a repo URL points at, falling back to gitlab.com."""
        parsed = urlparse(repo_url or "")
        if not parsed.scheme or not parsed.netloc:
            return self.url
        return f"{parsed.scheme}://{parsed.netloc}"

    def get_client(self, repo_url: str) -> Gitlab:
        """One client per instance, built on first use.

        GITLAB_TOKEN is a gitlab.com credential, so it is only ever sent
        there. A self-hosted instance gets an anonymous client, which is
        enough for the public projects we index.
        """
        if self.client is not None:
            return self.client

        base_url = self.get_base_url(repo_url)

        if base_url not in self._client_cache:
            token = settings.GITLAB_TOKEN if base_url == self.url else None
            self._client_cache[base_url] = Gitlab(base_url, private_token=token)

        return self._client_cache[base_url]

    def extract_repo_name(self, repo_url):
        """Everything after the host, since GitLab groups can nest."""
        parsed = urlparse(repo_url or "")
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path

    def _get_repo(self, repo_url):
        client = self.get_client(repo_url)
        return client.projects.get(self.extract_repo_name(repo_url), license=True)

    def _fetch_commit_stats(self, package, repo):
        client = self.get_client(package.repo_url)

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
        project_data = client.http_get(path)

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
