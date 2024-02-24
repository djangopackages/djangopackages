from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()


@register.filter(is_safe=True)
def markdown(text):
    md = MarkdownIt("gfm-like", {"linkify": True})
    return mark_safe(md.render(text))
