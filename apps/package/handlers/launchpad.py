import os

from django.conf import settings
from launchpadlib.launchpad import Launchpad

from package.handlers.base_handler import BaseHandler


class LaunchpadHandler(BaseHandler):
    title = 'Launchpad'
    url = 'https://code.launchpad.net'
    user_url = 'https://launchpad.net/~%s'
    repo_regex = r'https://code.launchpad.net/[\w\-\_]+/([\w\-\_]+)/[\w\-\_]+/{0,1}'
    slug_regex = r'https://code.launchpad.net/[\w\-\_]+/([\w\-\_]+)/[\w\-\_]+/{0,1}'

    def pull(self, package):
        cachedir = getattr(settings, 'LAUNCHPAD_CACHE_DIR', os.path.join(settings.PROJECT_ROOT, 'lp-cache'))
        launchpad = Launchpad.login_anonymously('djangopackages.com', 'production', cachedir)
        repo_name = package.repo_name()

        branch = launchpad.branches.getByUrl(url='lp:%s' % repo_name)

        package.repo_description = branch.description or ''
        package.repo_forks = len(branch.project.getBranches())
        package.repo_watchers = len(branch.subscribers)
        package.participants = branch.owner.name

        return package
