from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 
from django.views.decorators.csrf import csrf_protect

from package.forms import PackageForm
from package.models import Package


@login_required
@csrf_protect
def add_package(request, template_name="package/add_package.html"):
    
    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)    

    if form.is_valid(): 
        new_package = form.save()
        return HttpResponseRedirect(reverse('package', kwargs={'slug':new_package.slug}))
        

    return render_to_response(template_name, { 
        'form': form
        },
        context_instance=RequestContext(request))

@login_required
@csrf_protect
def edit_package(request, slug, template_name="package/edit_package.html"):

    package = get_object_or_404(Package, slug=slug)
    form = PackageForm(request.POST or None, instance=package)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('package', kwargs={'slug': package.slug}))

    return render_to_response(template_name, { 
        'form': form,  
        }, 
        context_instance=RequestContext(request))


