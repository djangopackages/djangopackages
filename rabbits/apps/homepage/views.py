
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 



from package.models import Package
from homepage.models import Dpotw, Gotw, Tab

def homepage(request, template_name="homepage.html"):
    
    packages = Package.objects.order_by('-pypi_downloads', '-repo_watchers', 'title')
    
    return render_to_response(template_name, {
        'packages': packages,
        'dpotw': Dpotw.objects.get_current(),
        'gotw': Gotw.objects.get_current(),
        'tab': Tab.objects.all()
        },
        context_instance=RequestContext(request)
        )