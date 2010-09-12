from django import template
from django.conf import settings
from django.template.defaultfilters import escape
from grid.models import Element
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
    return h.get(key, {})