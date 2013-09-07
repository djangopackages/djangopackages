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
            next_url = 'https://api.github.com/repos/{}/{}/commits'.format(
                username, repo_name
            )
            while next_url:
                self.stdout.write(next_url + "\n")
                response = requests.get(url=next_url,
                    auth=(settings.GITHUB_USERNAME, settings.GITHUB_PASSWORD)
                )
                if response.status_code == 200:
                    if 'next' in response.links:
                            next_url = response.links['next']['url']
                    else:
                        next_url = ''

                    commit = None
                    for commit in [x['commit'] for x in response.json()]:
                        try:
                            commit, created = Commit.objects.get_or_create(
                                package=package,
                                commit_date=commit['committer']['date']
                            )
                        except Commit.MultipleObjectsReturned:
                            pass

                    if commit is not None:
                        new_commit = Commit.objects.get(pk=commit.pk)
                        if new_commit.commit_date < timezone.now() - timezone.timedelta(days=365):
                            self.stdout.write("Last commit recorded at {}\n".format(commit.commit_date))
                            break
                else:
                    self.stdout.write("Status code is {}".format(response.status_code))
                    break

                package.last_fetched = timezone.now()
            package.save()
            self.stdout.write('Successfully fixed commits on "%s"' % package.slug)
