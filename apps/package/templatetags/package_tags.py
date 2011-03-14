from datetime import datetime, timedelta

from django import template

from package.models import Commit

from package.context_processors import used_packages_list

register = template.Library()

from django.core.cache import cache

@register.filter
def commits_over_52(package):

    now = datetime.now()
    commits = Commit.objects.filter(
        package=package,
        commit_date__gt=now - timedelta(weeks=52),
    ).values_list('commit_date', flat=True)

    weeks = [0] * 52
    for cdate in commits:
        age_weeks = (now - cdate).days // 7
        if age_weeks < 52:
            weeks[age_weeks] += 1

    return ','.join(map(str,reversed(weeks)))

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
