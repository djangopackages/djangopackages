from dataclasses import dataclass
import logging
from urllib.parse import urlparse

import httpx

from .base_handler import BaseHandler


logger = logging.getLogger(__name__)


@dataclass
class ForgejoMetadata:
    archived: bool
    archived_at: str | None
    description: str
    forks_count: int
    stars_count: int
    watchers_count: int


@dataclass
class ForgejoCommit:
    sha: str
    created: str
    user: str | None


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
            response.raise_for_status()
            data = response.json()
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

    def fetch_commits(self, repository: str, page_size=50):
        """Yield commit metadata for a repository."""
        current_page = 1

        while True:
            params = {"page": current_page, "limit": page_size}
            url = self._build_url(f"/repos/{repository}/commits")

            try:
                response = httpx.get(url, params=params)
                response.raise_for_status()
                commits = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.error("Failed to fetch %s with params %s: %s", url, params, exc)
                break

            for commit in commits:
                try:
                    yield ForgejoCommit(
                        sha=commit["sha"],
                        created=commit["created"],
                        user=commit.get("author", {}).get("login")
                        if commit.get("author")
                        else None,
                    )
                except KeyError:
                    logger.error(
                        "no created timestamp for %s with params %s", url, params
                    )
                    break

            if response.headers.get("x-hasmore") == "true":
                current_page = current_page + 1
            else:
                break


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

    def fetch_commits(self, package):
        from package.models import Commit

        client = self.get_client(package.repo_url)
        if client is None:
            return package

        collaborators = package.participants.split(",")

        if len(collaborators) == 1 and collaborators[0] == "":
            collaborators = []

        for commit in client.fetch_commits(package.repo_name()):
            try:
                _, created = Commit.objects.get_or_create(
                    package=package,
                    commit_hash=commit.sha,
                    commit_date=commit.created,
                )

                if not created:
                    break

                if commit.user:
                    collaborators.append(commit.user)
            except Commit.MultipleObjectsReturned:
                continue

        if len(collaborators) > 0:
            package.participants = ",".join(set(collaborators))

        package.save()

        return package

    def fetch_metadata(self, package):
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
        # TODO: consider adding "stargazers_count"
        # package.stargazers_count = repo.stars_count
        package.save()

        return package


repo_handler = ForgejoHandler()
