from django.test import TestCase

from grid.templatetags.grid_tags import (
    style_element,
    YES_IMG,
    NO_IMG,
    YES_KEYWORDS,
    NO_KEYWORDS,
)


class GridTest(TestCase):
    def test_01_style_element_filter(self):
        tests = [
            ("+", 1, 0, ""),
            ("++", 2, 0, ""),
            ("+++", 3, 0, ""),
            ("+1", 1, 0, ""),
            ("+2", 2, 0, ""),
            ("+3", 3, 0, ""),
            ("+4", 3, 0, ""),
            ("+42", 3, 0, ""),
            ("-", 0, 1, ""),
            ("--", 0, 2, ""),
            ("---", 0, 3, ""),
            ("-1", 0, 1, ""),
            ("-2", 0, 2, ""),
            ("-3", 0, 3, ""),
            ("-4", 0, 3, ""),
            ("-42", 0, 3, ""),
        ]
        for positive in YES_KEYWORDS:
            tests.append((positive, 1, 0, ""))
            tests.append((f"{positive}test", 1, 0, "test"))
        for negative in NO_KEYWORDS:
            tests.append((negative, 0, 1, ""))
            tests.append((f"{negative}test", 0, 1, "test"))
        for text, yes, no, endswith in tests:
            output = style_element(text)
            got_yes = output.count(YES_IMG)
            self.assertEqual(
                got_yes, yes, f"{text} resulted in {got_yes} yes-gifs instead of {yes}."
            )
            got_no = output.count(NO_IMG)
            self.assertEqual(
                got_no, no, f"{text} resulted in {got_no} no-gifs instead of {no}."
            )
            self.assertTrue(
                output.endswith(endswith),
                f"Expected {text} to end with {endswith}, got {output} instead.",
            )
