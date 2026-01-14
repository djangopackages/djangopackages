"""package.repos.base_handler

Base class for objects that interact with third-party code repository services.

In addition to per-provider API logic, this module centralizes commit aggregation
logic so all repo handlers update the same Package fields:

- Package.commits_over_52 (comma-separated 52-week histogram)
- Package.last_commit_date (date of most recent commit)
"""

import json
import re
from datetime import timedelta
import requests
from django.utils import timezone


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

    def fetch_metadata(self, package):
        """Accepts a package.models.Package instance:

            return: package.models.Package instance

        Must set the following fields:

            package.repo_watchers (int)
            package.repo_forks (int)
            package.repo_description (text )
            package.participants = (comma-separated value)

        """
        return NotImplemented

    def fetch_commits(self, package):
        """Accepts a package.models.Package instance:"""
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
        if r.status_code != 200:
            r.raise_for_status()
        return json.loads(r.content)

    def refresh_commit_stats(self, package, *, save=True):
        """Recompute `commits_over_52` and `last_commit_date` for a package.

        This reads from the Commit table (preferred for consistency) rather than
        provider responses.
        """

        from package.models import Commit

        now_dt = timezone.now()
        cutoff = now_dt - timedelta(weeks=52)

        latest_commit_dt = (
            Commit.objects.filter(package=package)
            .order_by("-commit_date")
            .values_list("commit_date", flat=True)
            .first()
        )

        if latest_commit_dt is not None:
            if timezone.is_aware(now_dt) and timezone.is_naive(latest_commit_dt):
                latest_commit_dt = timezone.make_aware(
                    latest_commit_dt, timezone.get_current_timezone()
                )
            elif timezone.is_naive(now_dt) and timezone.is_aware(latest_commit_dt):
                latest_commit_dt = timezone.make_naive(
                    latest_commit_dt, timezone.get_current_timezone()
                )

        package.last_commit_date = latest_commit_dt.date() if latest_commit_dt else None

        weeks = [0] * 52
        recent_commit_dates = (
            Commit.objects.filter(
                package=package,
                commit_date__gte=cutoff,
            )
            .values_list("commit_date", flat=True)
            .iterator()
        )

        for cdate in recent_commit_dates:
            if cdate is None:
                continue

            age_days = (now_dt - cdate).days
            if age_days < 0:
                continue
            age_weeks = age_days // 7
            if 0 <= age_weeks < 52:
                weeks[age_weeks] += 1

        # Store as oldest -> newest (52 values).
        package.commits_over_52 = ",".join(map(str, reversed(weeks)))

        if save:
            package.save()

        return package
