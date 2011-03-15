def get_handler(repo_id):
    mod = __import__("package.handlers." + repo_id)
    return getattr(mod.handlers, repo_id).handler


def get_handler_for_repo_url(repo_url):
    from package.handlers.github import handler as github_handler
    from package.handlers.unsupported import handler as unsupported_handler

    supported_handlers = (github_handler,)
    for handler in supported_handlers:
        if handler.repo_regex.match(repo_url):
            return handler

    return unsupported_handler


def supported_repos():
    return ["github"]
