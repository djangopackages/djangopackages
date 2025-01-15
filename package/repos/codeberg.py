from dataclasses import dataclass
import logging

import httpx

from .base_handler import BaseHandler


logger = logging.getLogger(__name__)


REPOSITORY_URL = "https://codeberg.org/api/v1/repos/{repository}"
COMMITS_URL = "https://codeberg.org/api/v1/repos/{repository}/commits"


@dataclass
class ForgejoMetadata:
    archived: bool
    archived_at: str | None
    description: str
    forks_count: int
    watchers_count: int


@dataclass
class ForgejoCommit:
    sha: str
    created: str
    user: str | None


class ForgejoClient:
    """Forgejos upper limit for pagination is 50 entities per page.

    The collaborator endpoint seems to have some issues, so it is not implemented.
    Collaborators are extracted from commits.
    """

    def fetch_repository(self, repository: str) -> ForgejoMetadata | None:
        try:
            url = REPOSITORY_URL.format(repository=repository)
            response = httpx.get(url)
        except Exception as exp:
            logger.error(exp)
            return None

        if response.status_code != httpx.codes.OK:
            logger.error(f"Response code: {response.status_code} for URL {url}")
            return None

        data = response.json()

        try:
            meta = ForgejoMetadata(
                archived=data["archived"],
                archived_at=data["archived_at"],
                description=data["description"],
                forks_count=data["forks_count"],
                watchers_count=data["watchers_count"],
            )
        except KeyError:
            logger.error("Key error for URL {url}")
            return None

        return meta

    def fetch_commits(self, repository: str, page_size=50):
        current_page = 1

        while True:
            params = {"page": current_page, "limit": page_size}

            url = COMMITS_URL.format(repository=repository)

            try:
                response = httpx.get(url, params=params)
            except Exception as exp:
                logger.error(exp)
                break

            if response.status_code != httpx.codes.OK:
                logger.error(
                    f"Response code: {response.status_code} for URL {url} with params {params}"
                )
                break

            for commit in response.json():
                try:
                    yield ForgejoCommit(
                        sha=commit["sha"],
                        created=commit["created"],
                        user=commit["author"]["login"]
                        if "author" in commit and commit["author"]
                        else None,
                    )
                except KeyError:
                    logger.error(f"no created timestamp for {url} with params {params}")
                    break

            if (
                "x-hasmore" in response.headers
                and response.headers["x-hasmore"] == "true"
            ):
                current_page = current_page + 1
            else:
                break


class CodebergHandler(BaseHandler):
    title = "Codeberg"
    url_regex = "(https|git)://codeberg.org/"
    url = "https://codeberg.org/"
    repo_regex = r"(?:https|git)://codeberg.org/[^/]*/([^/]*)"
    slug_regex = repo_regex

    def __init__(self):
        self.client = ForgejoClient()

    def fetch_commits(self, package):
        from package.models import Commit  # Added here to avoid circular imports

        # Use the existing list of participants and append all login names for
        # which commits are created. Before setting participants call `set()` to
        # ensure a participants login name only show up once.
        collaborators = package.participants.split(",")

        if len(collaborators) == 1 and collaborators[0] == "":
            collaborators = []

        for commit in self.client.fetch_commits(package.repo_name()):
            try:
                _, created = Commit.objects.get_or_create(
                    package=package,
                    commit_hash=commit.sha,
                    commit_date=commit.created,
                )

                # If the commit record already exists, it means we are at the end of the
                # list we want to import
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
        repo = self.client.fetch_repository(package.repo_name())

        if repo.archived:
            package.date_repo_archived = repo.archived_at

        package.repo_description = repo.description
        package.repo_forks = repo.forks_count
        package.repo_watchers = repo.watchers_count
        package.save()

        return package


repo_handler = CodebergHandler()
