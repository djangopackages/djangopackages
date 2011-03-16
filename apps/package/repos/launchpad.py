import datetime
import os

from bzrlib.branch import Branch
from django.conf import settings
from launchpadlib.launchpad import Launchpad

from .base_handler import BaseHandler


class LaunchpadHandler(BaseHandler):
    title = 'Launchpad'
    url = 'https://code.launchpad.net'
    user_url = 'https://launchpad.net/~%s'
    repo_regex = r'https://code.launchpad.net/~[\w\-\_]+/([\w\-\_]+)/[\w\-\_]+/{0,1}'
    slug_regex = r'https://code.launchpad.net/~[\w\-\_]+/([\w\-\_]+)/[\w\-\_]+/{0,1}'

    def fetch_commits(self, package):
        from package.models import Commit # Import placed here to avoid circular dependencies
        branch = Branch.open(package.repo_url)
        repository = branch.repository
        for revision_id in branch.revision_history():
            revision = repository.get_revision(revision_id)
            timestamp = datetime.datetime.fromtimestamp(revision.timestamp)
            commit, created = Commit.objects.get_or_create(package=package, commit_date=timestamp)

    def fetch_metadata(self, package):
        cachedir = getattr(settings, 'LAUNCHPAD_CACHE_DIR', os.path.join(settings.PROJECT_ROOT, 'lp-cache'))
        launchpad = Launchpad.login_anonymously('djangopackages.com', 'production', cachedir)
        repo_name = package.repo_name()

        branch = launchpad.branches.getByUrl(url='lp:%s' % repo_name)

        package.repo_description = branch.description or ''
        package.repo_forks = len(branch.project.getBranches())
        package.repo_watchers = len(branch.subscribers)
        package.participants = branch.owner.name

        return package

repo_handler = LaunchpadHandler()
