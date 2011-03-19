from django.test import TestCase

from pypi.models import PypiUpdateLog

class LogTests(TestCase):

    def test_last_update_empty(self):
        self.assertEquals(PypiUpdateLog.last_update(), None)
    
    def test_log_create(self):
        
        log = PypiUpdateLog()
        log.save()
        self.assertEquals(PypiUpdateLog.objects.count(), 1)
        
    def test_last_update_logs(self):
        log = PypiUpdateLog()
        log.save()        
        self.assertTrue(PypiUpdateLog.last_update())
        print PypiUpdateLog.last_update()
        