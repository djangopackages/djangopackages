from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 


from package.forms import PackageForm, PackageExampleForm
from package.models import Package, PackageExample


@login_required
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


def add_example(request, slug, template_name="package/add_example.html"):
    
    package = get_object_or_404(Package, slug=slug)
    new_package_example = PackageExample()
    form = PackageExampleForm(request.POST or None, instance=new_package_example)    

    if form.is_valid():
        package_example = PackageExample(package=package,
                title=request.POST['title'],
                url=request.POST['url'])
        package_example.save()
        return HttpResponseRedirect(reverse('package', kwargs={'slug':package_example.package.slug}))
        

    return render_to_response(template_name, { 
        'form': form
        },
        context_instance=RequestContext(request))    


def edit_example(request, slug, id, template_name="package/edit_example.html"):

    package_example = get_object_or_404(PackageExample, id=id)
    form = PackageExampleForm(request.POST or None, instance=package_example)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('package', kwargs={'slug': package_example.package.slug}))

    return render_to_response(template_name, { 
        'form': form,  
        }, 
        context_instance=RequestContext(request))
    