def get_repo(repo_id):
    mod = __import__("package.handlers." + repo_id)
    return getattr(mod.handlers, repo_id).repo_handler

def supported_repos():
    return ["github"]
