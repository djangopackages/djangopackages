"""
Base class for objects that interact with third-party code repository services.
"""

import json
import re
from datetime import timedelta

import requests
from django.utils import timezone


class RepoRateLimitError(Exception):
    pass


def get_week_index(date_obj):
    """Returns an absolute week index for a given date (Mon-based)."""
    return (date_obj.toordinal() - 1) // 7


class BaseHandler:
    supports_auto_detection = True

    def __str__(self):
        return self.title

    @property
    def title(self):
        """title for display in drop downs:

        return: string
        example: 'GitHub'
        """
        return NotImplemented

    @property
    def url(self):
        """base value for url API interaction:

        return: URL string
        example: 'https://github.com'
        """
        return NotImplemented

    def fetch_metadata(self, package, *, save: bool = True):
        """Accepts a package.models.Package instance:

            return: package.models.Package instance

        Must set the following fields:

            package.repo_watchers (int)
            package.repo_forks (int)
            package.repo_description (text )
            package.participants = (comma-separated value)

        """
        return NotImplemented

    @property
    def is_other(self):
        """DON'T CHANGE THIS PROPERTY! This should only be overridden by
        the unsupported handler.

                return: False
        """
        return False

    @property
    def user_url(self):
        """identifies the user URL:

        example:
        """
        return ""

    @property
    def repo_regex(self):
        """Used by the JavaScript forms"""
        return NotImplemented

    @property
    def slug_regex(self):
        """Used by the JavaScript forms"""
        return NotImplemented

    def extract_repo_name(self, repo_url):
        """Return the repository path (e.g. owner/repo) for a given URL."""
        if not repo_url:
            return ""
        return re.sub(self.url_regex, "", repo_url)

    def packages_for_profile(self, profile):
        """Return a list of all packages contributed to by a profile."""
        if repo_url := profile.url_for_repo(self):
            from package.models import Package

            regex = r"^{0},|,{0},|{0}$".format(repo_url)
            return list(
                Package.objects.filter(
                    participants__regex=regex, repo_url__regex=self.repo_regex
                )
            )
        else:
            return []

    def serialize(self):
        return {
            "title": self.title,
            "url": self.url,
            "repo_regex": self.repo_regex,
        }

    def get_json(self, target):
        """
        Helpful utility method to do a quick GET for JSON data.
        """
        r = requests.get(target)
        if r.status_code == 429:
            raise RepoRateLimitError("repo rate limit reached")
        if r.status_code != 200:
            r.raise_for_status()
        return json.loads(r.content)

    def _get_commits_update_params(self, package):
        """
        Calculates the parameters needed for updating commit statistics.

        Goal: Decide *what* to fetch.

        Logic:
            It checks if we already have data (`commits_over_52w`) and when we last fetched it (`last_fetched`).

        Incremental Update:
            If the last fetch was recent (within the last year), it tells the handler to only fetch commits
            *since* that last fetch date.

        Full Fetch:
            If it's a new package or the data is stale/missing, it defaults to fetching the full last 52 weeks.

        Returns:
            A tuple: `(start_date, is_incremental)`.
        """
        now = timezone.now()

        # Conditions for incremental update:
        # 1. We have existing data (commits_over_52w is not empty)
        # 2. We have a last_fetched timestamp
        # 3. last_fetched is within the last 52 weeks (approx)

        if (
            package.commits_over_52w
            and package.last_fetched
            and package.last_fetched > (now - timedelta(weeks=52))
        ):
            # Incremental: fetch since last_fetched (+ 1 second to avoid double counting)
            return package.last_fetched + timedelta(seconds=1), True

        # Full fetch: last 52 weeks
        since_date = now - timedelta(weeks=52)
        return since_date, False

    def _process_commit_counts(self, package, commit_dates, is_incremental):
        """
        Updates the `commits_over_52w` list (which is a list of 52 integers, representing weekly commit counts).

        Goal: Update the commit counts list with new data.

        Logic:
            If Incremental:
                It calculates how many weeks have passed since the last update. It "shifts" the existing list
                to the left (dropping old weeks) and fills the new gap with zeros. Then, it places the newly
                fetched commits into their correct weekly buckets.
            If Full Fetch:
                It starts with a fresh list of 52 zeros and populates it from scratch.

        Result:
            `package.commits_over_52w` is updated with the latest data, correctly aligned to the current week.
        """
        now = timezone.now()
        current_week_index = get_week_index(now)

        if is_incremental:
            # Shift existing data
            last_fetched_week = get_week_index(package.last_fetched)
            weeks_diff = current_week_index - last_fetched_week

            commits_over_52w = package.commits_over_52w or []
            if weeks_diff > 0:
                # Shift left: drop oldest 'weeks_diff', append 'weeks_diff' zeros
                # If weeks_diff >= 52, the list becomes all zeros
                if weeks_diff >= len(commits_over_52w):
                    commits_over_52w = [0] * 52
                else:
                    commits_over_52w = commits_over_52w[weeks_diff:] + [0] * weeks_diff
        else:
            # Fresh start
            commits_over_52w = [0] * 52

        # Add new commits
        for date_obj in commit_dates:
            # Ensure date_obj is timezone-aware and normalized if needed
            # Assuming handlers provide aware datetimes or we don't care about hour-level precision for weeks

            c_week = get_week_index(date_obj)

            # Index 51 is current week
            # Index 50 is current week - 1
            # ...
            # Index = 51 - (current_week_index - c_week)

            offset = current_week_index - c_week
            index = 51 - offset

            if 0 <= index < 52:
                commits_over_52w[index] += 1

        package.commits_over_52w = commits_over_52w
