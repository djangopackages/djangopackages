import simplejson

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext

from package.models import Package, Category
from importer.importers import import_from_github_acct


@login_required
def import_github(request, template_name="importer/github.html"):
    
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    results = []
    if request.method == 'POST':
        github_name = request.POST.get('github_name')
        user_type = request.POST.get('user_type')
        category_slug = request.POST.get('category_slug')
        results = import_from_github_acct(github_name, user_type, category_slug)

    return render_to_response(template_name,
                {'results':results,
                'categories':Category.objects.all()},
                context_instance=RequestContext(request))
