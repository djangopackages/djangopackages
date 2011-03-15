from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from apps.package.models import Package, Repo



class GitHubTest(TestCase):

    fixtures = ['test_initial_data.json']

    def test_repos(self):
        print Repo.objects.all()