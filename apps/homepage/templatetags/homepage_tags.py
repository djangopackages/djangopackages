from django import template

from homepage.models import Tab

register = template.Library()

@register.tag(name="get_tabs")
def get_tabs(parser, token):
    
    return GetElementNode()
    
class GetElementNode(template.Node):
    
        def __init__(self):
            pass
            
        def render(self, context):
            context['tabs'] = Tab.objects.all().select_related('grid')
            return ''