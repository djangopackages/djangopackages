from datetime import timedelta
from datetime import datetime

from django import template

from github2.client import Github

from package.models import Package

register = template.Library()

github = Github()

@register.filter
def commits_over_52(package):
    # TODO - make this work with other repo types
    
    current = datetime.now()
    weeks = []
    commits = [x.committed_date for x in github.commits.list(package.repo_name(), "master")]
    for week in range(52):
        weeks.append(len([x for x in commits if x < current and x > (current - timedelta(7))]))
        current -= timedelta(7)        

    weeks.reverse()
    weeks = [str(x) for x in weeks]
    return ','.join(weeks)
    
@register.tag(name="list_all_packages")
def list_all_packages(parser, token):
    return ListAllPackagesNode()
    
class ListAllPackagesNode(template.Node):
        def __init__(self):
            pass
        def render(self, context):
            return Package.objects.all()