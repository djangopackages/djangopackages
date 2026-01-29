from dataclasses import dataclass
import logging
from urllib.parse import urlparse
from datetime import datetime

import httpx
import requests

from .base_handler import BaseHandler, RepoRateLimitError


logger = logging.getLogger(__name__)


@dataclass
class ForgejoMetadata:
    archived: bool
    archived_at: str | None
    description: str
    forks_count: int
    stars_count: int
    watchers_count: int


class ForgejoClient:
    """Client for interacting with Forgejo instances."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.api_base_url = f"{self.base_url}/api/v1"

    def _build_url(self, path: str) -> str:
        return f"{self.api_base_url}{path}"

    def fetch_repository(self, repository: str) -> ForgejoMetadata | None:
        url = self._build_url(f"/repos/{repository}")
        try:
            response = httpx.get(url)
            if response.status_code == 429:
                raise RepoRateLimitError("forgejo rate limit reached")
            response.raise_for_status()
            data = response.json()
        except RepoRateLimitError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return None

        try:
            return ForgejoMetadata(
                archived=data["archived"],
                archived_at=data.get("archived_at"),
                description=data.get("description", ""),
                forks_count=data.get("forks_count", 0),
                stars_count=data.get("stars_count", 0),
                watchers_count=data.get("watchers_count", 0),
            )
        except KeyError as exc:
            logger.error("Key error %s for URL %s", exc, url)
            return None


class ForgejoHandler(BaseHandler):
    title = "Forgejo"
    url = "https://forgejo.org"
    # Regex is broad enough for manual validation; auto-detection is disabled.
    url_regex = r"(?:https|git)://[^/]+/"
    repo_regex = r"(?:https|git)://[^/]+/[^/]+/[^/]+/?"
    slug_regex = repo_regex
    supports_auto_detection = False

    def __init__(self):
        self.client = None
        self.client_class = ForgejoClient
        self._client_cache: dict[str, ForgejoClient] = {}

    def extract_repo_name(self, repo_url):
        parsed = urlparse(repo_url or "")
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path

    def get_base_url(self, repo_url: str) -> str:
        parsed = urlparse(repo_url or "")
        if not parsed.scheme or not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}"

    def get_client(self, repo_url: str) -> ForgejoClient | None:
        if self.client is not None:
            return self.client

        base_url = self.get_base_url(repo_url)
        if not base_url:
            return None

        if base_url not in self._client_cache:
            self._client_cache[base_url] = self.client_class(base_url)

        return self._client_cache[base_url]

    def _fetch_commit_stats(self, package):
        owner, repo_name = package.repo_name().split("/")
        base_url = self.get_base_url(package.repo_url)

        # Fetch the most recent commit
        commits_url = f"{base_url}/api/v1/repos/{owner}/{repo_name}/commits?limit=1"
        resp = requests.get(commits_url)
        resp.raise_for_status()
        last_commit = resp.json()[0]
        package.last_commit_date = datetime.fromisoformat(
            last_commit["commit"]["committer"]["date"].replace("Z", "+00:00")
        )

        # Forgejo provides total count in response header
        package.commit_count = int(resp.headers.get("X-Total-Count", 0))

        # Build a 52-week histogram by fetching commits from the past year (or incrementally)
        since_date, is_incremental = self._get_commits_update_params(package)
        since_str = since_date.isoformat()
        if not since_str.endswith("Z") and "+" not in since_str:
            since_str += "Z"

        commits_url = f"{base_url}/api/v1/repos/{owner}/{repo_name}/commits?since={since_str}&limit=100"
        all_commits = []
        page = 1

        while True:
            resp = requests.get(f"{commits_url}&page={page}")
            resp.raise_for_status()
            commits = resp.json()
            if not commits:
                break
            all_commits.extend(commits)
            page += 1

        commit_dates = []
        for commit in all_commits:
            commit_dates.append(
                datetime.fromisoformat(
                    commit["commit"]["committer"]["date"].replace("Z", "+00:00")
                )
            )

        self._process_commit_counts(package, commit_dates, is_incremental)

    def fetch_metadata(self, package, *, save: bool = True):
        client = self.get_client(package.repo_url)
        if client is None:
            return package

        repo = client.fetch_repository(package.repo_name())

        if repo is None:
            return package

        if repo.archived:
            package.date_repo_archived = repo.archived_at

        package.repo_description = repo.description
        package.repo_forks = repo.forks_count
        package.repo_watchers = repo.watchers_count

        self._fetch_commit_stats(package)

        if save:
            package.save()

        return package


repo_handler = ForgejoHandler()
