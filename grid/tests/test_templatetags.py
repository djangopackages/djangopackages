from django.test import TestCase

from grid.templatetags.grid_tags import (
    NO_ICON,
    NO_KEYWORDS,
    YES_ICON,
    YES_KEYWORDS,
    style_element,
)


class GridTest(TestCase):
    def test_01_style_element_filter(self):
        tests = [
            ("+", 1, 0, "", YES_ICON),
            ("++", 2, 0, "", YES_ICON * 2),
            ("+++", 3, 0, "", YES_ICON * 3),
            ("+1", 1, 0, "", YES_ICON),
            ("+2", 2, 0, "", YES_ICON * 2),
            ("+3", 3, 0, "", YES_ICON * 3),
            ("+4", 3, 0, "", YES_ICON * 3),
            ("+42", 3, 0, "", YES_ICON * 3),
            ("-", 0, 1, "", NO_ICON),
            ("--", 0, 2, "", NO_ICON * 2),
            ("---", 0, 3, "", NO_ICON * 3),
            ("-1", 0, 1, "", NO_ICON),
            ("-2", 0, 2, "", NO_ICON * 2),
            ("-3", 0, 3, "", NO_ICON * 3),
            ("-4", 0, 3, "", NO_ICON * 3),
            ("-42", 0, 3, "", NO_ICON * 3),
        ]
        for positive in YES_KEYWORDS:
            tests.append((positive, 1, 0, "", YES_ICON))
            tests.append((f"{positive}test", 1, 0, "test", None))
        for negative in NO_KEYWORDS:
            tests.append((negative, 0, 1, "", NO_ICON))
            tests.append((f"{negative}test", 0, 1, "test", None))

        for text, yes, no, endswith, exact_output in tests:
            with self.subTest(text=text):
                output = style_element(text)
                got_yes = output.count(YES_ICON)
                got_no = output.count(NO_ICON)
                self.assertEqual(
                    got_yes,
                    yes,
                    f"{text} resulted in {got_yes} yes-icons instead of {yes}.",
                )
                self.assertEqual(
                    got_no,
                    no,
                    f"{text} resulted in {got_no} no-icons instead of {no}.",
                )
                self.assertTrue(
                    output.endswith(endswith),
                    f"Expected {text} to end with {endswith}, got {output} instead.",
                )
                if exact_output is not None:
                    self.assertEqual(output, exact_output)
