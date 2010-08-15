
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 
from django.views.decorators.csrf import csrf_protect


from package.models import Package
from homepage.models import Dpotw, Gotw, Tab

def homepage(request, template_name="homepage.html"):
    
    return render_to_response(template_name, {
        'packages': Package.objects.all(),
        'dpotw': Dpotw.objects.get_current(),
        'gotw': Gotw.objects.get_current(),
        'tab': Tab.objects.all()
        },
        context_instance=RequestContext(request)
        )