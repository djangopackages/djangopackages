"""template tags and filters
for the :mod:`grid` app"""

import re

from django import template
from django.conf import settings
from django.template.defaultfilters import escape, truncatewords
from django.template.loader import render_to_string

register = template.Library()

static_url = settings.STATIC_URL

plus_two_re = re.compile(r"^(\+2|\+{2})$")
minus_two_re = re.compile(r"^(\-2|\-{2})$")

plus_three_re = re.compile(r"^(\+[3-9]{1,}|\+{3,}|\+[1-9][0-9]+)$")
minus_three_re = re.compile(r"^(\-[3-9]{1,}|\-{3,}|\-[1-9][0-9]+)$")

YES_KEYWORDS = ("check", "yes", "good", "+1", "+")
NO_KEYWORDS = ("bad", "negative", "evil", "sucks", "no", "-1", "-")

# Tailwind + Phosphor icons
YES_ICON = '<span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/10"><i class="ph-bold ph-check text-emerald-600 dark:text-emerald-400 text-xs"></i></span>'
NO_ICON = '<span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-rose-500/10"><i class="ph-bold ph-x text-rose-600 dark:text-rose-400 text-xs"></i></span>'


@register.filter
def style_element(text):
    """Style element text with icons based on keywords.

    Args:
        text: The element text to style
    """
    low_text = text.strip().lower()
    if low_text in YES_KEYWORDS:
        return YES_ICON
    if low_text in NO_KEYWORDS:
        return NO_ICON

    if plus_two_re.search(low_text):
        return YES_ICON * 2

    if minus_two_re.search(low_text):
        return NO_ICON * 2

    if plus_three_re.search(low_text):
        return YES_ICON * 3

    if minus_three_re.search(low_text):
        return NO_ICON * 3

    text = escape(text)

    found = False
    for positive in YES_KEYWORDS:
        if text.startswith(positive):
            text = f"{YES_ICON}&nbsp;{text[len(positive) :]}"
            found = True
            break
    if not found:
        for negative in NO_KEYWORDS:
            if text.startswith(negative):
                text = f"{NO_ICON}&nbsp;{text[len(negative) :]}"
                break

    return text


@register.filter
def hash(h, key):
    """Function leaves considerable overhead in the grid_detail views.
    each element of the list results in two calls to this hash function.
    Code there, and possible here, should be refactored.
    """
    return h.get(key, {})


@register.filter
def style_attribute(attribute_name, package):
    mappings = {
        "title": style_title,
        "repo_description": style_repo_description,
        "commits_over_52": style_commits,
    }

    as_var = template.Variable("package." + attribute_name)
    try:
        value = as_var.resolve({"package": package})
    except template.VariableDoesNotExist:
        value = ""

    if attribute_name in list(mappings.keys()):
        return mappings[attribute_name](value)

    return style_default(value)


@register.filter
def style_title(value):
    value = value[:20]
    return render_to_string("grid/snippets/_title.html", {"value": value})


def style_commits(value):
    return render_to_string(
        "package/includes/_commits.html", {"value": value, "graph_width": 45}
    )


@register.filter
def style_description(value):
    return style_default(value[:20])


@register.filter
def style_default(value):
    return value


@register.filter
def style_repo_description(var):
    truncated_desc = truncatewords(var, 20)
    return truncated_desc


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key.

    Usage: {{ element_map|get_item:feature.pk|get_item:package.pk }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    """Multiply a value by an argument.

    Usage: {{ 20|multiply:-1 }}
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
