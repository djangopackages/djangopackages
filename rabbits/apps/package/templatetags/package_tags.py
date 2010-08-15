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
    
    if 'github' in package.repo.title.lower():
    
        current = datetime.now()
        weeks = []
        commits = [x.committed_date for x in github.commits.list(package.repo_name(), "master")]
        for week in range(52):
            weeks.append(len([x for x in commits if x < current and x > (current - timedelta(7))]))
            current -= timedelta(7)        

        weeks.reverse()
        weeks = [str(x) for x in weeks]
        return ','.join(weeks)
        
    else:
        
        return ','.join(('0' for x in range(52)))