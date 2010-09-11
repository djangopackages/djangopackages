import re

from django import template
from django.conf import settings
from django.template.defaultfilters import escape

from grid.models import Element

register = template.Library()

static_url = settings.STATIC_URL

plus_two_re = re.compile(r'(^\+2$|\+{2})')
minus_two_re = re.compile(r'(^\-2$|\-{2})')

plus_three_re = re.compile(r'^(\+[3-9]{1,}|\+{3,}|\+[1-9][0-9]+)$')
minus_three_re = re.compile(r'^(\-[3-9]{1,}|\-{3,}|\-[1-9][0-9]+)$')

@register.filter
def style_element(text):
    low_text = text.strip().lower()
    if low_text in ('check', 'yes', 'good', '+1', '+'):
        return '<img src="%simg/icon-yes.gif" />' % settings.STATIC_URL
    if low_text in ('bad', 'negative', 'evil', 'sucks', 'no', '-1', '-'):
        return '<img src="%simg/icon-no.gif" />' % settings.STATIC_URL

    if plus_two_re.search(low_text):
        return '<img src="%simg/icon-yes.gif" />' % settings.STATIC_URL * 2

    if minus_two_re.search(low_text):
        return '<img src="%simg/icon-no.gif" />' % settings.STATIC_URL * 2

    if plus_three_re.search(low_text):
        return '<img src="%simg/icon-yes.gif" />' % settings.STATIC_URL * 3

    if minus_three_re.search(low_text):
        return '<img src="%simg/icon-no.gif" />' % settings.STATIC_URL * 3

    # TODO Find the Django method that does this for me.
    text = text.replace('&','&amp;')
    text = text.replace('<','&lt;').replace('>',' &gt;')
    text = text.replace("'",'&#39;').replace('"','&quot;')    

    
    return text
    
@register.filter
def hash(h, key):
    return h.get(key, {})