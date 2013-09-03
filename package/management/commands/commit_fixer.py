from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

import requests
from github3 import login

from package.models import Package, Commit

github = login(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)


class Command(BaseCommand):
    args = '<package_slug package_slug ...>'
    help = 'Fixes the commits for a package'

    def handle(self, *args, **options):
        for slug in args:
            try:
                package = Package.objects.get(slug=slug)
            except Package.DoesNotExist:
                raise CommandError('Package "%s" does not exist' % slug)

            while github.ratelimit_remaining < 10:
                self.stdout.write("Sleeping...")
                sleep(1)

            repo_name = package.repo_name()
            if repo_name.endswith("/"):
                repo_name = repo_name[:-1]
            try:
                username, repo_name = package.repo_name().split('/')
            except ValueError:
                self.stdout.write('Bad GitHub link on "%s"' % package)
                continue

            self.stdout.write('Getting old GitHub commits for "%s"\n' % package)
            data = [1, ]
            page = 0
            last_sha = ""
            while len(data):
                commit = None
                page += 1
                url = 'https://api.github.com/repos/{}/{}/commits?per_page=100'.format(
                        username, repo_name
                    )
                if last_sha:
                    url += "&last_sha={}".format(last_sha)
                self.stdout.write(url + "\n")
                r = requests.get(
                    url=url,
                    auth=(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
                )
                if r.status_code == 200:
                    print "COMPARE", data == r.json()
                    data = r.json()
                    for commit in [x['commit'] for x in data]:
                        commit, created = Commit.objects.get_or_create(
                            package=package,
                            commit_date=commit['committer']['date']
                        )
                        last_sha = data[:-1][0]['sha']
                    if commit:
                        print commit.commit_date

                package.last_fetched = timezone.now()
                package.save()
                if page > 8:
                    break
            self.stdout.write('Successfully fixed commits on "%s"' % package)
