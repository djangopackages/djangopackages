from package.handlers.base_handler import BaseHandler

class UnsupportedHandler(BaseHandler):
    title = 'Other'
    is_other = True
    url = ''
    user_url = ''

    def pull(self, package):
        package.repo_watchers    = 0
        package.repo_forks       = 0
        package.repo_description = ''
        package.participants     = ''

repo_handler = UnsupportedHandler()
