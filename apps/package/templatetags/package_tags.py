from datetime import datetime, timedelta

from django import template

from package.models import Commit

from package.context_processors import used_packages_list

register = template.Library()

from django.core.cache import cache


class ParticipantURLNode(template.Node):

    def __init__(self, repo, participant):
        self.repo = template.Variable(repo)
        self.participant = template.Variable(participant)

    def render(self, context):
        repo = self.repo.resolve(context)
        participant = self.participant.resolve(context)
        if repo.user_url:
            user_url = repo.user_url % participant
        else:
            user_url = '%s/%s' % (repo.url, participant)
        return user_url


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


@register.tag
def participant_url(parser, token):
    try:
        tag_name, repo, participant = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    return ParticipantURLNode(repo, participant)


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
