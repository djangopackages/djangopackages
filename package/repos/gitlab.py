from django.conf import settings
from django.utils import timezone
from gitlab import Gitlab

from .base_handler import BaseHandler


class GitlabHandler(BaseHandler):
    title = "GitLab"
    url_regex = "(http|https|git)://gitlab.com/"
    url = "https://gitlab.com"
    repo_regex = r"(?:http|https|git)://gitlab.com/[^/]*/([^/]*)"
    slug_regex = repo_regex
    gitlab: Gitlab

    def __init__(self):
        if settings.GITLAB_TOKEN:
            self.gitlab = Gitlab(self.url, private_token=settings.GITLAB_TOKEN)
        else:
            self.gitlab = Gitlab(self.url)

    def _get_repo(self, repo_url):
        path = repo_url.replace(f"{self.url}/", "")
        return self.gitlab.projects.get(path, license=True)

    def fetch_metadata(self, package):
        repo = self._get_repo(package.repo_url)
        if repo is None:
            return package

        if hasattr(repo, "archived"):
            if repo.archived:
                if not package.date_repo_archived:
                    package.date_repo_archived = timezone.now()

        package.repo_watchers = repo.star_count
        package.repo_forks = repo.forks_count
        package.repo_description = repo.description
        print(repo.badges.list())

        return package

    def fetch_commits(self, package):
        repo = self._get_repo(package.repo_url)
        if repo is None:
            return package

        from package.models import Commit  # Added here to avoid circular imports

        for commit in repo.commits.list(as_list=False):
            try:
                commit_record, created = Commit.objects.get_or_create(
                    package=package,
                    commit_date=commit.committed_date,
                    commit_hash=commit.id,
                )
                if not created:
                    break
            except Commit.MultipleObjectsReturned:
                continue
            # If the commit record already exists, it means we are at the end of the
            #   list we want to import

        package.save()
        return package


repo_handler = GitlabHandler()
