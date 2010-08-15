import re

from django import template
from django.conf import settings

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

    # TODO Replace this with SafeString class cause this SUCKS hard for security
    text = text.replace('<','[').replace('>',']')
    
    return text
    

@register.tag(name="get_or_create_grid_element")
def get_or_create_grid_element(parser, token):
    try:
        tag_name, grid_package, feature = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly three arguments" % token.contents.split()[0]
        
    return GetElementNode(grid_package, feature)
    
class GetElementNode(template.Node):
    
        def __init__(self, grid_package, feature):
            self.grid_package   = template.Variable(grid_package)
            self.feature        = template.Variable(feature)
            
        def render(self, context):
            grid_package = self.grid_package.resolve(context)
            feature      = self.feature.resolve(context)            
            context['element'], created = Element.objects.get_or_create(
                                            grid_package=grid_package,
                                            feature=feature
                                            )
            return ''