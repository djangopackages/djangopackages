from django.test import TestCase
from package.models import Package
from package.signals import signal_fetch_latest_metadata

class SignalTests(TestCase):
    sender_name = ''
    def test_fetch_metadata(self):
        p = Package.objects.create(slug='dummy')
        def handle_signal(sender, **kwargs):
            self.sender_name = sender.slug
        signal_fetch_latest_metadata.connect(handle_signal)
        p.fetch_metadata()
        self.assertEquals(self.sender_name, 'dummy')
