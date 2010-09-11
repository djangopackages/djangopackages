from datetime import timedelta
from datetime import datetime

from django import template

from github2.client import Github

from package.models import Package, Commit

register = template.Library()

github = Github()

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
