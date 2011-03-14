import os

from django.conf import settings

from launchpadlib.launchpad import Launchpad


def pull(package):
    
    cachedir = getattr(settings, 'LAUNCHPAD_CACHE_DIR', os.path.join(settings.PROJECT_ROOT, 'lp-cache'))
    launchpad = Launchpad.login_anonymously('djangopackages.com', 'production', cachedir)
    repo_name = package.repo_name().replace('https://code.launchpad.net/','')

    branch = launchpad.branches.getByUrl(url='lp:%s' % repo_name)


    package.repo_description = branch.description or ''
    package.repo_forks = len(branch.project.getBranches())
    package.repo_watchers = len(branch.subscribers)
    package.participants = branch.owner.name

    return package
