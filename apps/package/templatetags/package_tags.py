from datetime import datetime, timedelta

from django import template

from package.models import Commit

from package.context_processors import used_packages_list

register = template.Library()

from django.core.cache import cache

@register.filter
def commits_over_52(package):

    current = datetime.now()
    weeks = []
    commits = Commit.objects.filter(package=package).values_list('commit_date', flat=True)
    for week in range(52):
        weeks.append(len([x for x in commits if x < current and x > (current - timedelta(7))]))
        current -= timedelta(7)        

    weeks.reverse()
    weeks = map(str, weeks)
    return ','.join(weeks)

@register.inclusion_tag('package/templatetags/_usage_button.html', takes_context=True)
def usage_button(context):
    response = used_packages_list(context['request'])
    response['STATIC_URL'] = context['STATIC_URL']
    response['package'] = context['package']
    if context['package'].pk in response['used_packages_list']:
        response['usage_action'] = "remove"
        response['image'] = "usage_triangle_filled"
    else:
        response['usage_action'] = "add"
        response['image'] = "usage_triangle_hollow"    
    return response