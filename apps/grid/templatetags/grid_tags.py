"""template tags and filters
for the :mod:`apps.grid` app"""
from django import template
from django.conf import settings
from django.template.defaultfilters import escape, truncatewords
from grid.models import Element
from django.template.loader import render_to_string

import re

register = template.Library()

static_url = settings.STATIC_URL

plus_two_re = re.compile(r'^(\+2|\+{2})$')
minus_two_re = re.compile(r'^(\-2|\-{2})$')

plus_three_re = re.compile(r'^(\+[3-9]{1,}|\+{3,}|\+[1-9][0-9]+)$')
minus_three_re = re.compile(r'^(\-[3-9]{1,}|\-{3,}|\-[1-9][0-9]+)$')

YES_KEYWORDS = ('check', 'yes', 'good', '+1', '+')
NO_KEYWORDS = ('bad', 'negative', 'evil', 'sucks', 'no', '-1', '-')
YES_IMG = '<img src="%simg/icon-yes.gif" />' % settings.STATIC_URL
NO_IMG = '<img src="%simg/icon-no.gif" />' % settings.STATIC_URL

@register.filter
def style_element(text):
    low_text = text.strip().lower()
    if low_text in YES_KEYWORDS:
        return YES_IMG
    if low_text in NO_KEYWORDS:
        return NO_IMG

    if plus_two_re.search(low_text):
        return YES_IMG * 2

    if minus_two_re.search(low_text):
        return NO_IMG * 2

    if plus_three_re.search(low_text):
        return YES_IMG * 3

    if minus_three_re.search(low_text):
        return NO_IMG * 3
    
    text = escape(text)
    
    found = False
    for positive in YES_KEYWORDS:
        if text.startswith(positive):
            text = '%s&nbsp;%s' % (YES_IMG, text[len(positive):])
            found = True
            break
    if not found:
        for negative in NO_KEYWORDS:
            if text.startswith(negative):
                text = '%s&nbsp;%s' % (NO_IMG, text[len(negative):])
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
            'title': style_title,
            'repo_description': style_repo_description,
            'commits_over_52': style_commits,
    }

    as_var = template.Variable('package.' + attribute_name)
    try:
        value = as_var.resolve({'package': package})
    except template.VariableDoesNotExist:
        value = ''

    if attribute_name in mappings.keys():
        return  mappings[attribute_name](value)

    return style_default(value)

@register.filter
def style_title(value):
    value = value[:20]
    return render_to_string('grid/snippets/_title.html', { 'value': value })

def style_commits(value):
    return render_to_string('grid/snippets/_commits.html', { 'value': value })

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

