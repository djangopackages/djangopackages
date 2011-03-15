import re


def get_repo(repo_id):
    mod = __import__("package.handlers." + repo_id)
    return getattr(mod.handlers, repo_id).repo_handler


def get_handler_for_repo_url(repo_url):
    from package.handlers.github import repo_handler as github_handler
    from package.handlers.launchpad import repo_handler as launchpad_handler
    from package.handlers.unsupported import repo_handler as unsupported_handler

    supported_handlers = (github_handler, launchpad_handler)
    for handler in supported_handlers:
        if re.match(handler.repo_regex, repo_url):
            return handler

    return unsupported_handler


def supported_repos():
    return ["github", "launchpad"]
