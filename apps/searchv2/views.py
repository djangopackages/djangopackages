from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext

from searchv2.builders import build_1

@login_required
def build_search(request, template_name="searchv2/build_results.html"):
    
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    
    results = build_1()

    return render_to_response(template_name,{'results':results},context_instance=RequestContext(request))