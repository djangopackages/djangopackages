from package.handlers.base_handler import BaseHandler


def pull(package):
    
    package.repo_watchers    = 0
    package.repo_forks       = 0
    package.repo_description = ''
    package.participants     = ''    
    
    return package


class UnsupportedHandler(BaseHandler):
    is_other = True

repo_handler = UnsupportedHandler()
