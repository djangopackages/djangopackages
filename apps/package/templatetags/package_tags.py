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
    commits = [x.commit_date for x in Commit.objects.filter(package=package)]
    for week in range(52):
        weeks.append(len([x for x in commits if x < current and x > (current - timedelta(7))]))
        current -= timedelta(7)        

    weeks.reverse()
    weeks = [str(x) for x in weeks]
    return ','.join(weeks)
    
@register.inclusion_tag('package/templatetags/usage.html')
def usage(user, package):
    
    using = package.usage.filter(username=user) or False
    count = 0
    if using:
        count = package.usage.count() - 1
            
    return {
                "using": using,
                "count": count,
                "package_id": package.id,
                "user_id": user.id,
            }