from github2.client import Github

from package.utils import uniquer

def pull(package):

    github   = Github()
    repo_name = package.repo_name()
    repo         = github.repos.show(repo_name)
    package.repo_watchers    = repo.watchers
    package.repo_forks       = repo.forks
    package.repo_description = repo.description

    collaborators = github.repos.list_collaborators(repo_name) + [x['login'] for x in github.repos.list_contributors(repo_name)]
    if collaborators:
        package.participants = ','.join(uniquer(collaborators))
        
    return package
