import simplejson

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext


from package.forms import PackageForm, PackageExampleForm
from package.models import Category, Package, PackageExample, Repo

def repos_for_js():
    repos = {}
    for repo in Repo.objects.all():
        repos[repo.url] = repo.id
    return simplejson.dumps(repos)  

@login_required
def add_package(request, template_name="package/package_form.html"):
    
    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)
    
    if form.is_valid():
        new_package = form.save()
        return HttpResponseRedirect(reverse("package", kwargs={"slug":new_package.slug}))
    
    return render_to_response(template_name, {
        "form": form,
        "repos": repos_for_js(),
        "action": "add",
        },
        context_instance=RequestContext(request))

@login_required
def edit_package(request, slug, template_name="package/package_form.html"):
    
    package = get_object_or_404(Package, slug=slug)
    form = PackageForm(request.POST or None, instance=package)
    
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))
    
    return render_to_response(template_name, {
        "form": form,
        "package": package,
        "repos": repos_for_js(),
        "action": "edit",
        },
        context_instance=RequestContext(request))

@login_required
def update_package(request, slug):
    
    package = get_object_or_404(Package, slug=slug)
    package.save()
        
    return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))



def add_example(request, slug, template_name="package/add_example.html"):
    
    package = get_object_or_404(Package, slug=slug)
    new_package_example = PackageExample()
    form = PackageExampleForm(request.POST or None, instance=new_package_example)
    
    if form.is_valid():
        package_example = PackageExample(package=package,
                title=request.POST["title"],
                url=request.POST["url"])
        package_example.save()
        return HttpResponseRedirect(reverse("package", kwargs={"slug":package_example.package.slug}))

    
    return render_to_response(template_name, {
        "form": form,
        "package":package
        },
        context_instance=RequestContext(request))


def edit_example(request, slug, id, template_name="package/edit_example.html"):
    
    package_example = get_object_or_404(PackageExample, id=id)
    form = PackageExampleForm(request.POST or None, instance=package_example)
    
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("package", kwargs={"slug": package_example.package.slug}))
    
    return render_to_response(template_name, {
        "form": form,
        "package":package_example.package
        },
        context_instance=RequestContext(request))


def package_autocomplete(request):
    """
    Provides Package matching based on matches of the beginning
    """
    titles = []
    q = request.GET.get("q", "")
    if q:
        titles = (x.title for x in Package.objects.filter(title__istartswith=q))
    
    response = HttpResponse("\n".join(titles))
    
    setattr(response, "djangologging.suppress_output", True)
    return response

def category(request, slug, template_name="package/category.html"):
    category = get_object_or_404(Category, slug=slug)
    used_packages = ()
    if request.user.is_authenticated():
        used_packages = request.user.package_set.filter(category=category).values_list("pk", flat=True)
    
    packages = category.package_set.annotate(usage_count=Count("usage")).order_by("-pypi_downloads", "-repo_watchers", "title")
    return render_to_response(template_name, {
        "category": category,
        "packages": packages,
        "used_packages": used_packages,
        },
        context_instance=RequestContext(request)
    )

def ajax_package_list(request, template_name="package/ajax_package_list.html"):
    q = request.GET.get("q","")
    packages = []
    if q:
        django_dash = "django-%s" % q
        django_space = "django %s" % q
        packages = Package.objects.filter(
                        Q(title__istartswith=q) |
                        Q(title__istartswith=django_dash) |
                        Q(title__istartswith=django_space)
                    )
    return render_to_response(template_name, {
        "packages": packages
        },
        context_instance=RequestContext(request)
    )
    
def usage(request, package_id, user_id):
    package = get_object_or_404(Package, id=package_id)
    user = get_object_or_404(User, id=user_id)
    
    # user wants to be taken off
    if package.usage.filter(username=user.username):
        package.usage.remove(user)
    else:    
        package.usage.add(user)
    
    #return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))
    return HttpResponseRedirect(request.META["HTTP_REFERER"])