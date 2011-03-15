from django.conf import settings
from github2.client import Github
from package.utils import uniquer
from base_handler import BaseHandler

class GitHubHandler(BaseHandler):
    title = "Github"
    url = "https://github.com"
    user_url = ""
    repo_regex = r'https://github.com/[\w\-\_]+/([\w\-\_]+)/{0,1}'
    slug_regex = r'https://github.com/[\w\-\_]+/([\w\-\_]+)/{0,1}'

    def pull(self, package):
        if hasattr(settings, "GITHUB_ACCOUNT") and hasattr(settings, "GITHUB_KEY"):
            github   = Github(username=settings.GITHUB_ACCOUNT, api_token=settings.GITHUB_KEY)
        else:
            github   = Github()

        repo_name = package.repo_name
        repo = github.repos.show(repo_name)
        package.repo_watchers    = repo.watchers
        package.repo_forks       = repo.forks
        package.repo_description = repo.description

        collaborators = github.repos.list_collaborators(repo_name) + [x['login'] for x in github.repos.list_contributors(repo_name)]
        if collaborators:
            package.participants = ','.join(uniquer(collaborators))

repo_handler = GitHubHandler()
