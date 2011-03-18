from random import randrange
import simplejson
import urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string

from homepage.models import Dpotw, Gotw

from package.forms import PackageForm, PackageExampleForm
from package.models import Category, Package, PackageExample
from package.repos import get_all_repos


def repo_data_for_js():
    repos = [handler.serialize() for handler in get_all_repos()]
    return simplejson.dumps(repos)


@login_required
def add_package(request, template_name="package/package_form.html"):
    
    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)
    
    if form.is_valid():
        new_package = form.save()
        new_package.created_by = request.user
        new_package.last_modified_by = request.user
        new_package.save()
        new_package.fetch_metadata()
        return HttpResponseRedirect(reverse("package", kwargs={"slug":new_package.slug}))
    
    return render_to_response(template_name, {
        "form": form,
        "repo_data": repo_data_for_js(),
        "action": "add",
        },
        context_instance=RequestContext(request))

@login_required
def edit_package(request, slug, template_name="package/package_form.html"):
    
    package = get_object_or_404(Package, slug=slug)
    form = PackageForm(request.POST or None, instance=package)
    
    if form.is_valid():
        modified_package = form.save()
        modified_package.last_modified_by = request.user
        modified_package.save()
        
        return HttpResponseRedirect(reverse("package", kwargs={"slug": modified_package.slug}))
    
    return render_to_response(template_name, {
        "form": form,
        "package": package,
        "repo_data": repo_data_for_js(),
        "action": "edit",
        },
        context_instance=RequestContext(request))

@login_required
def update_package(request, slug):
    
    package = get_object_or_404(Package, slug=slug)
    package.fetch_metadata()
    messages.add_message(request, messages.INFO, 'Package updated successfully')
        
    return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))


@login_required
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

@login_required
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
    packages = category.package_set.annotate(usage_count=Count("usage")).order_by("-pypi_downloads", "-repo_watchers", "title")
    return render_to_response(template_name, {
        "category": category,
        "packages": packages,
        },
        context_instance=RequestContext(request)
    )

def ajax_package_list(request, template_name="package/ajax_package_list.html"):
    q = request.GET.get("q","")
    packages = []
    if q:
        django_dash = "%s-%s" % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
        django_space = "%s %s" % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
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

def usage(request, slug, action):
    success = False
    # Check if the user is authenticated, redirecting them to the login page if
    # they're not.
    if not request.user.is_authenticated():
        url = settings.LOGIN_URL + '?next=%s' % reverse('usage', args=(slug, action))
        referer = request.META.get('HTTP_REFERER')
        if referer:
            url += urllib.quote_plus('?next=/%s' % referer.split('/', 3)[-1])
        
        if request.is_ajax():
            response = {}
            response['success'] = success
            response['redirect'] = url
            return HttpResponse(simplejson.dumps(response))
        return HttpResponseRedirect(url)
    
    package = get_object_or_404(Package, slug=slug)
    
    # Update the current user's usage of the given package as specified by the
    # request.
    if package.usage.filter(username=request.user.username):
        if action.lower() == 'remove':
            package.usage.remove(request.user)
            success = True
            template_name = 'package/add_usage_button.html'
            change = -1
    else:
        if action.lower() == 'add':
            package.usage.add(request.user)
            success = True
            template_name = 'package/remove_usage_button.html'
            change = 1
    
    # Invalidate the cache of this users's used_packages_list.
    if success:
        cache_key = "sitewide_used_packages_list_%s" % request.user.pk
        cache.delete(cache_key)
    
    # Return an ajax-appropriate response if necessary
    if request.is_ajax():
        response = {'success': success}
        if success:
            response['change'] = change
            response['body'] = render_to_string(
                template_name,
                {"package": package},
            )
        return HttpResponse(simplejson.dumps(response))
    
    # Intelligently determine the URL to redirect the user to based on the
    # available information.
    next = request.GET.get('next') or request.META.get("HTTP_REFERER") or reverse("package", kwargs={"slug": package.slug})
    return HttpResponseRedirect(next)
    
def packaginate(request):
    """ Special project method - DO NOT TOUCH!!! """

    packages = Package.objects.all()
    package = packages[randrange(0, packages.count())]
    response = dict(
            title = package.title,
            url = package.get_absolute_url(),
            description=package.repo_description
        )
    return HttpResponse(simplejson.dumps(response))    

def package_list(request, template_name="package/package_list.html"):

    categories = []
    for category in Category.objects.annotate(package_count=Count("package")):
        element = {
            "title":category.title,
            "description":category.description,
            "count": category.package_count,
            "slug": category.slug,
            "title_plural": category.title_plural,
            "show_pypi": category.show_pypi,
            "packages": category.package_set.annotate(usage_count=Count("usage")).order_by("-pypi_downloads", "-repo_watchers", "title")[:9]
        }
        categories.append(element)

    return render_to_response(
        template_name, {
            "categories": categories,
            "dpotw": Dpotw.objects.get_current(),
            "gotw": Gotw.objects.get_current(),
        }, context_instance = RequestContext(request)
    )
