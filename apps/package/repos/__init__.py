import re

def get_repo(repo_id):
    mod = __import__("package.repos." + repo_id)
    return getattr(mod.repos, repo_id).repo_handler

def get_repo_for_repo_url(repo_url):
    for handler in (get_repo(repo_id) for repo_id in supported_repos()):
        if re.match(handler.repo_regex, repo_url):
            return handler

    from package.repos.unsupported import repo_handler as unsupported_handler
    return unsupported_handler

def supported_repos():
    return ["github", "launchpad"]
