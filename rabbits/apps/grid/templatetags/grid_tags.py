from django import template

from grid.models import Element

register = template.Library()

@register.filter
def style_element(text):
    if text.strip().lower() == 'check':
        return '[check]'

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