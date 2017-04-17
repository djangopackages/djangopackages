from django.test import TestCase
from package.models import Package, Category
from package.signals import signal_fetch_latest_metadata


class SignalTests(TestCase):
    sender_name = ''

    def test_fetch_metadata(self):
        category = Category.objects.create(
                        title='dumb category',
                        slug='blah'
                        )
        category.save()
        package = Package.objects.create(slug='dummy', category=category)

        def handle_signal(sender, **kwargs):
            self.sender_name = sender.slug
        signal_fetch_latest_metadata.connect(handle_signal)
        package.fetch_metadata()
        self.assertEqual(self.sender_name, 'dummy')
