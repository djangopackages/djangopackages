from package.handlers.base_handler import BaseHandler


def pull(package):
    
    package.repo_watchers    = 0
    package.repo_forks       = 0
    package.repo_description = ''
    package.participants     = ''    
    
    return package


class UnsupportedHandler(BaseHandler):

    @property
    def is_other(self):
        return True

handler = UnsupportedHandler()
