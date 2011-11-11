import importlib
from random import randrange
import simplejson
import urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Q, Count, get_model
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, render
from django.template import RequestContext

from homepage.models import Dpotw, Gotw

from grid.models import Grid
from package.forms import PackageForm, PackageExampleForm
from package.models import Category, Package, PackageExample
from package.repos import get_all_repos


def repo_data_for_js():
    repos = [handler.serialize() for handler in get_all_repos()]
    return simplejson.dumps(repos)
    
def get_form_class(form_name):
    bits = form_name.split('.')
    form_module_name = '.'.join(bits[:-1])
    form_module = importlib.import_module(form_module_name)
    form_name = bits[-1]
    return getattr(form_module, form_name)
    
    
def build_package_extenders(request):
    """ package extenders machinery 
            TODO: change the ID prefix in this form to be unique
    
    """
    package_extenders = []
    for item in getattr(settings, "PACKAGE_EXTENDERS", []):
        package_extenders_dict = {}
        form_class = get_form_class(item['form'])        
        if 'model' in item:
            app_name, app_model = item['model'].split('.')
            package_extenders_dict['model'] = get_model(app_name, app_model)
            package_extenders_dict['model_instance'] = package_extenders_dict['model']()
            package_extenders_dict['form'] = form_class(request.POST or None, instance=package_extenders_dict['model_instance'])
        else:
            package_extenders_dict['form'] = form_class(request.POST or None)
        package_extenders.append(package_extenders_dict)    
    return package_extenders


@login_required
def add_package(request, template_name="package/package_form.html"):

    if not request.user.get_profile().can_add_package:
        return HttpResponseForbidden("permission denied")


    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)
    
    package_extenders = build_package_extenders(request)
        
    if form.is_valid():
        new_package = form.save()
        new_package.created_by = request.user
        new_package.last_modified_by = request.user
        new_package.save()
        new_package.fetch_metadata()
        
        # stick in package_extender form processing
        for package_extender in package_extenders:
            if package_extender['form'].is_valid():
                package_extender['form'].save()        
        return HttpResponseRedirect(reverse("package", kwargs={"slug":new_package.slug}))
    
    return render(request, template_name, {
        "form": form,
        "repo_data": repo_data_for_js(),
        "action": "add",
        "package_extenders":package_extenders
        })

@login_required
def edit_package(request, slug, template_name="package/package_form.html"):
    
    if not request.user.get_profile().can_edit_package:
        return HttpResponseForbidden("permission denied")

    package = get_object_or_404(Package, slug=slug)
    form = PackageForm(request.POST or None, instance=package)
    
    package_extenders = build_package_extenders(request)    
    
    if form.is_valid():
        modified_package = form.save()
        modified_package.last_modified_by = request.user
        modified_package.save()    
        # stick in package_extender form processing
        for package_extender in package_extenders:
            if package_extender['form'].is_valid():
                package_extender['form'].save()            
        return HttpResponseRedirect(reverse("package", kwargs={"slug": modified_package.slug}))
    
    return render(request, template_name, {
        "form": form,
        "package": package,
        "repo_data": repo_data_for_js(),
        "action": "edit",
        })

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

    
    return render(request, template_name, {
        "form": form,
        "package":package
        })

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
        _dash = "%s-%s" % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
        _space = "%s %s" % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
        _underscore = '%s_%s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)          
        packages = Package.objects.filter(
                        Q(title__istartswith=q) |
                        Q(title__istartswith=_dash) |
                        Q(title__istartswith=_space) | 
                        Q(title__istartswith=_underscore)
                    )
                    
    packages_already_added_list = []
    grid_slug = request.GET.get("grid","")
    if packages and grid_slug:
        grids = Grid.objects.filter(slug=grid_slug)
        if grids:
            grid = grids[0]
            packages_already_added_list = [x['slug'] for x in grid.packages.all().values('slug')]
            new_packages = tuple(packages.exclude(slug__in=packages_already_added_list))[:20]
            number_of_packages = len(new_packages)
            if number_of_packages < 20:
                try:
                    old_packages = packages.filter(slug__in=packages_already_added_list)[:20-number_of_packages]
                except AssertionError:
                    old_packages = None
                    
                if old_packages:
                    old_packages = tuple(old_packages)
                    packages = new_packages + old_packages
            else:
                packages = new_packages

    return render_to_response(template_name, {
        "packages": packages,
        'packages_already_added_list':packages_already_added_list,
        },
        context_instance=RequestContext(request)
    )

def usage(request, slug, action):
    success = False
    # Check if the user is authenticated, redirecting them to the login page if
    # they're not.
    if not request.user.is_authenticated():
        
        url = settings.LOGIN_URL
        referer = request.META.get('HTTP_REFERER')
        if referer:
            url += urllib.quote_plus('?next=/%s' % referer.split('/', 3)[-1])
        else:
            url += '?next=%s' % reverse('usage', args=(slug, action))
        url = reverse("login")
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
        if action.lower() == 'add':
            # The user is already using the package
            success = True
            change = 0
        else:
            # If the action was not add and the user has already specified 
            # they are a use the package then remove their usage.
            package.usage.remove(request.user)
            success = True
            change = -1
    else:
        if action.lower() == 'lower':
            # The user is not using the package
            success = True
            change = 0 
        else:
            # If the action was not lower and the user is not already using 
            # the package then add their usage.
            package.usage.add(request.user)
            success = True
            change = 1
    
    # Invalidate the cache of this users's used_packages_list.
    if change == 1 or change == -1:
        cache_key = "sitewide_used_packages_list_%s" % request.user.pk
        cache.delete(cache_key)
    
    # Return an ajax-appropriate response if necessary
    if request.is_ajax():
        response = {'success': success}
        if success:
            response['change'] = change
            
        return HttpResponse(simplejson.dumps(response))
    
    # Intelligently determine the URL to redirect the user to based on the
    # available information.
    next = request.GET.get('next') or request.META.get("HTTP_REFERER") or reverse("package", kwargs={"slug": package.slug})
    return HttpResponseRedirect(next)
    

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

def package_detail(request, slug, template_name="package/package.html"):
    
    package = get_object_or_404(Package, slug=slug)
    no_development = package.no_development
    try:
        if package.category == Category.objects.get(slug='projects'):
            # projects get a bye because they are a website
            pypi_ancient = False
            pypi_no_release = False
        else:
            pypi_ancient = package.pypi_ancient
            pypi_no_release = package.pypi_ancient is None
        warnings = no_development or pypi_ancient or pypi_no_release
    except Category.DoesNotExist:
        pypi_ancient = False
        pypi_no_release = False
        warnings = no_development
    
    return render(request, template_name, 
            dict(
                package = package,
                pypi_ancient=pypi_ancient,
                no_development=no_development,
                pypi_no_release=pypi_no_release,
                warnings=warnings
                
            )
        )





