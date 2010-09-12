"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.conf import settings
from django.test import TestCase
from grid.templatetags.grid_tags import style_element, YES, NO

class GridTest(TestCase):
    def test_01_style_element_filter(self):
        tests = [
            ('+', 1, 0, ''),
            ('++', 2, 0, ''),
            ('+++', 3, 0, ''),
            ('+1', 1, 0, ''),
            ('+2', 2, 0, ''),
            ('+3', 3, 0, ''),
            ('+4', 3, 0, ''),
            ('+42', 3, 0, ''),
            ('-', 0, 1, ''),
            ('--', 0, 2, ''),
            ('---', 0, 3, ''),
            ('-1', 0, 1, ''),
            ('-2', 0, 2, ''),
            ('-3', 0, 3, ''),
            ('-4', 0, 3, ''),
            ('-42', 0, 3, ''),
            ('+test', 1, 0, 'test'),
            ('-test', 0, 1, 'test'),
        ]
        for positive in YES:
            tests.append((positive, 1, 0, ''))
        for negative in NO:
            tests.append((negative, 0, 1, ''))
        for text, yes, no, endswith in tests:
            output = style_element(text)
            got_yes = output.count('<img src="%simg/icon-yes.gif" />' % settings.STATIC_URL)
            self.assertEqual(
                got_yes,
                yes,
                "%s resulted in %s yes-gifs instead of %s." % (text, got_yes, yes)
            )
            got_no = output.count('<img src="%simg/icon-no.gif" />' % settings.STATIC_URL)
            self.assertEqual(
                got_no,
                no,
                "%s resulted in %s no-gifs instead of %s." % (text, got_no, no)
            )
            self.assertTrue(
                output.endswith(endswith),
                "Expected %s to end with %s, got %s instead." % (text, endswith, output)
            )