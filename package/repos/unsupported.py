from .base_handler import BaseHandler


class UnsupportedHandler(BaseHandler):
    title = 'Other'
    is_other = True
    url_regex = ''
    url = ''

    def fetch_metadata(self, package):
        package.repo_watchers = 0
        package.repo_forks = 0
        package.repo_description = ''
        package.participants = ''

    def fetch_commits(self, package):
        package.commit_set.all().delete()


repo_handler = UnsupportedHandler()
