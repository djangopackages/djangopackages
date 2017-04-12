from datetime import datetime

from django.test import TestCase

from searchv2.models import SearchV2


class SearchV2Test(TestCase):

    def test_create(self):
        SearchV2.objects.create(
            item_type='package',
            title='Django Uni-Form',
            title_no_prefix='uni-form',
            slug='django-uni-form',
            slug_no_prefix='uni-form',
            clean_title='uniform',
            description="Blah blah blah",
            category='app',
            absolute_url='/packages/p/django-uni-form/',
            repo_watchers=500,
            repo_forks=85,
            pypi_downloads=30000,
            participants="pydanny,maraujop,et,al",
            last_committed=datetime.now(),
            last_released=datetime.now(),
        )
        self.assertEqual(SearchV2.objects.count(), 1)
