from .base_handler import BaseHandler


class UnsupportedHandler(BaseHandler):
    title = "Other"
    is_other = True
    url_regex = ""
    url = ""

    def fetch_metadata(self, package, save=True):
        package.repo_watchers = 0
        package.repo_forks = 0
        package.repo_description = ""
        package.participants = ""

        self._fetch_commit_stats(package, None)

        if save:
            package.save()
        return package

    def _fetch_commit_stats(self, package, repo):
        package.commits_over_52w = []
        package.last_commit_date = None
        package.commit_count = 0


repo_handler = UnsupportedHandler()
