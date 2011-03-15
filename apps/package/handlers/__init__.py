def get_handler(repo_id):
    mod = __import__("package.handlers." + repo_id)
    return getattr(mod.handlers, repo_id).handler

def supported_repos():
    return ["github"]
