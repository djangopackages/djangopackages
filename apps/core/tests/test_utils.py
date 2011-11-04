from django.test import TestCase

from core import utils

class SlugifyOC(TestCase):
    
    def test_oc_slugify(self):
        
        lst = (
            ('test.this.value', 'test-this-value'),
            ('Plone.OpenComparison', 'plone-opencomparison'),
            ('Run from here', 'run-from-here'),
            ('Jump_the shark', 'jump_the-shark'),                                
            )
            
        for l in lst:
            self.assertEquals(utils.oc_slugify(l[0]), l[1])
            
    def test_oc_slugify_fail(self):
        # TODO - fill this in
        pass