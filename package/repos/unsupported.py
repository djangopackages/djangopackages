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

        if save:
            package.save()
        return package

    def fetch_commits(self, package, save=True):
        package.commit_set.all().delete()
        package.commits_over_52 = ""
        package.last_commit_date = None

        if save:
            package.save()
        return package

    def refresh_commit_stats(self, package, *, save: bool = True):
        package.commits_over_52 = []
        package.last_commit_date = None

        if save:
            package.save()


repo_handler = UnsupportedHandler()
