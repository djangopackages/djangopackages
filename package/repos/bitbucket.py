from datetime import datetime
from warnings import warn

import requests

from .base_handler import BaseHandler

API_TARGET = "https://api.bitbucket.org/2.0/repositories"


class BitbucketHandler(BaseHandler):
    title = "Bitbucket"
    url_regex = "https://bitbucket.org/"
    url = "https://bitbucket.org"
    repo_regex = r"https://bitbucket.org/[\w\-\_]+/([\w\-\_]+)/{0,1}"
    slug_regex = r"https://bitbucket.org/[\w\-\_]+/([\w\-\_]+)/{0,1}"

    def _fetch_commit_stats(self, package):
        workspace, repo_slug = package.repo_name().split("/")
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"

        # Fetch the most recent commit
        commits_url = f"{base_url}/commits?pagelen=1"
        resp = requests.get(commits_url)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("values"):
            return package

        last_commit = data["values"][0]
        package.last_commit_date = datetime.fromisoformat(
            last_commit["date"].replace("Z", "+00:00")
        )

        # Calculate total commits by paginating through all commits
        # TODO: Optimize this either by not showing total commits for Bitbucket
        # showing approximate count.
        # Alternatively, fetch all commits for the first time and store commit sha
        # then afterwards only fetch commits since last known sha to update count.
        total_commits = 0
        next_url = f"{base_url}/commits?pagelen=100"
        while next_url:
            resp = requests.get(next_url)
            resp.raise_for_status()
            page_data = resp.json()
            total_commits += len(page_data.get("values", []))
            next_url = page_data.get("next")
        package.commit_count = total_commits

        # Build a 52-week histogram (incremental)
        since_date, is_incremental = self._get_commits_update_params(package)
        since_str = since_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        next_url = f"{base_url}/commits?since={since_str}&pagelen=100"
        all_commits = []
        while next_url:
            resp = requests.get(next_url)
            resp.raise_for_status()
            data = resp.json()
            all_commits.extend(data.get("values", []))
            next_url = data.get("next")

        commit_dates = []
        for commit in all_commits:
            commit_dates.append(
                datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
            )

        self._process_commit_counts(package, commit_dates, is_incremental)

    def fetch_metadata(self, package, *, save: bool = True):
        repo_name = package.repo_name()
        target = f"{API_TARGET}/{repo_name}"
        if not target.endswith("/"):
            target += "/"

        try:
            data = self.get_json(target)
        except requests.exceptions.HTTPError:
            return package

        if data is None:
            warn(f"{package.title} had a JSONDecodeError during bitbucket.repo.pull")
            return package

        package.repo_description = data.get("description", "")

        try:
            package.repo_forks = len(self.get_json(f"{target}forks/")["values"])
            package.repo_watchers = len(self.get_json(f"{target}watchers/")["values"])
        except (requests.exceptions.HTTPError, ValueError, KeyError):
            pass  # Let's not fail the whole thing if we can't get forks/watchers

        try:
            package.participants = package.repo_url.split("/")[3]
        except IndexError:
            package.participants = ""

        self._fetch_commit_stats(package)

        if save:
            package.save()

        return package


repo_handler = BitbucketHandler()
