# -*- coding: utf-8 -*-
from core.test_utils.context_managers import SettingsOverride
from django import template
from django.test.testcases import TestCase


class PackaginatorTagsTests(TestCase):
    def test_fixed_ga(self):
        tpl = template.Template("""
            {% load packaginator_tags %}
            {% fixed_ga %}
        """)
        context = template.Context()
        
        with SettingsOverride(URCHIN_ID='testid', DEBUG=False):
            output = tpl.render(context)
            self.assertTrue('var pageTracker = _gat._getTracker("testid");' in output)
        
        with SettingsOverride(URCHIN_ID='testid', DEBUG=True):
            output = tpl.render(context)
            self.assertEqual(output.strip(), "")
        
        with SettingsOverride(URCHIN_ID=None, DEBUG=True):
            output = tpl.render(context)
            self.assertEqual(output.strip(), "")
        
        with SettingsOverride(URCHIN_ID=None, DEBUG=False):
            output = tpl.render(context)
            self.assertEqual(output.strip(), "")