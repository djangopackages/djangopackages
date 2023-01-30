import importlib
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django_tables2 import SingleTableView

from grid.models import Grid
from homepage.models import Dpotw, Gotw
from package.forms import (
    PackageForm,
    PackageExampleForm,
    DocumentationForm,
    FlaggedPackageForm,
)
from package.models import Category, FlaggedPackage, Package, PackageExample
from package.repos import get_all_repos
from package.tables import PackageTable, PackageByCategoryTable


def repo_data_for_js():
    repos = [handler.serialize() for handler in get_all_repos()]
    return json.dumps(repos)


def get_form_class(form_name):
    bits = form_name.split(".")
    form_module_name = ".".join(bits[:-1])
    form_module = importlib.import_module(form_module_name)
    form_name = bits[-1]
    return getattr(form_module, form_name)


@login_required
def add_package(request, template_name="package/package_form.html"):

    if not request.user.profile.can_add_package:
        return HttpResponseForbidden("permission denied")

    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)

    if form.is_valid():
        new_package = form.save()
        new_package.created_by = request.user
        new_package.last_modified_by = request.user
        new_package.save()
        # new_package.fetch_metadata()
        # new_package.fetch_commits()

        return HttpResponseRedirect(
            reverse("package", kwargs={"slug": new_package.slug})
        )

    return render(
        request,
        template_name,
        {
            "form": form,
            "repo_data": repo_data_for_js(),
            "action": "add",
        },
    )


@login_required
def edit_package(request, slug, template_name="package/package_form.html"):

    if not request.user.profile.can_edit_package:
        return HttpResponseForbidden("permission denied")

    package = get_object_or_404(Package, slug=slug)
    form = PackageForm(request.POST or None, instance=package)

    if form.is_valid():
        modified_package = form.save()
        modified_package.last_modified_by = request.user
        modified_package.save()
        messages.add_message(request, messages.INFO, "Package updated successfully")
        return HttpResponseRedirect(
            reverse("package", kwargs={"slug": modified_package.slug})
        )

    return render(
        request,
        template_name,
        {
            "form": form,
            "package": package,
            "repo_data": repo_data_for_js(),
            "action": "edit",
        },
    )


@login_required
def update_package(request, slug):

    package = get_object_or_404(Package, slug=slug)
    package.fetch_metadata()
    package.fetch_commits()
    package.last_fetched = timezone.now()
    messages.add_message(request, messages.INFO, "Package updated successfully")

    return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))


@login_required
def flag_package(request, slug, template_name="package/flag_form.html"):

    package = get_object_or_404(Package, slug=slug)
    form = FlaggedPackageForm(request.POST or None)

    if form.is_valid():
        flagged_package = form.save(commit=False)
        flagged_package.user = request.user
        flagged_package.package = package
        flagged_package.save()
        messages.add_message(
            request, messages.INFO, "Flag submission submitted for review"
        )
        return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))

    return render(request, template_name, {"form": form})


def flag_approve(request, slug):
    flag = get_object_or_404(FlaggedPackage, package__slug=slug)
    flag.approve()
    messages.add_message(request, messages.INFO, "Flag approved")
    return HttpResponseRedirect(reverse("package", kwargs={"slug": flag.package.slug}))


def flag_remove(request, slug):
    flag = get_object_or_404(FlaggedPackage, package__slug=slug)
    flag.delete()
    messages.add_message(request, messages.INFO, "Flag removed")
    return HttpResponseRedirect(reverse("package", kwargs={"slug": flag.package.slug}))


@login_required
def add_example(request, slug, template_name="package/add_example.html"):

    package = get_object_or_404(Package, slug=slug)
    new_package_example = PackageExample()
    form = PackageExampleForm(request.POST or None, instance=new_package_example)

    if form.is_valid():
        package_example = PackageExample(
            package=package,
            title=request.POST["title"],
            url=request.POST["url"],
            created_by=request.user,
        )
        package_example.save()
        return HttpResponseRedirect(
            reverse("package", kwargs={"slug": package_example.package.slug})
        )

    return render(request, template_name, {"form": form, "package": package})


@login_required
def edit_example(request, slug, id, template_name="package/edit_example.html"):

    package_example = get_object_or_404(PackageExample, id=id)
    form = PackageExampleForm(request.POST or None, instance=package_example)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(
            reverse("package", kwargs={"slug": package_example.package.slug})
        )

    return render(
        request, template_name, {"form": form, "package_example": package_example}
    )


@login_required
def delete_example(request, slug, id, template_name="package/delete_example.html"):

    package_example = get_object_or_404(
        PackageExample, id=id, package__slug__iexact=slug
    )
    if package_example.created_by is None and not request.user.is_staff:
        raise PermissionDenied
    if package_example.created_by.id != request.user.id and not request.user.is_staff:
        raise PermissionDenied

    return render(request, template_name, {"package_example": package_example})


@login_required
@require_POST
def confirm_delete_example(request, slug, id):

    package_example = get_object_or_404(
        PackageExample, id=id, package__slug__iexact=slug
    )
    if package_example.created_by.id != request.user.id and not request.user.is_staff:
        raise PermissionDenied

    package_example.delete()
    messages.add_message(
        request, messages.INFO, "Package example successfully deleted."
    )

    return HttpResponseRedirect(reverse("package", kwargs={"slug": slug}))


class PackageByCategoryListView(SingleTableView):
    table_class = PackageByCategoryTable
    template_name = "package/category.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["category"] = get_object_or_404(Category, slug=self.kwargs["slug"])
        return context_data

    def get_queryset(self):
        packages = (
            Package.objects.filter(category__slug=self.kwargs["slug"])
            .select_related(
                "category",
                "created_by",
                "last_modified_by",
                "deprecated_by",
                "deprecates_package",
            )
            .annotate(usage_count=Count("usage"))
            .order_by("-repo_watchers", "title")
        )
        return packages


def category(request, slug, template_name="package/category.html"):
    direction = request.GET.get("dir")
    sort = request.GET.get("sort")

    """
    These are workarounds primarily search engine spiders trying weird
    sorting options when they are crawling the website.
    """
    _mutable = request.GET._mutable
    request.GET._mutable = True
    request.GET = request.GET.copy()

    # workaround for "blank" ?sort=desc bug
    if direction == "desc" and sort is None:
        request.GET["dir"] = ""
        request.GET["sort"] = ""

    elif direction and direction.lower() not in ["", "asc", "desc"]:
        request.GET["dir"] = ""

    request.GET._mutable = _mutable

    category = get_object_or_404(Category, slug=slug)
    packages = (
        category.package_set.select_related(
            "category",
            "created_by",
            "last_modified_by",
            "deprecated_by",
            "deprecates_package",
        )
        .annotate(usage_count=Count("usage"))
        .order_by("-repo_watchers", "title")
    )
    return render(
        request,
        template_name,
        {
            "category": category,
            "packages": packages,
        },
    )


def ajax_package_list(request, template_name="package/ajax_package_list.html"):
    q = request.GET.get("q", "")
    packages = []
    if q:
        _dash = f"{settings.PACKAGINATOR_SEARCH_PREFIX}-{q}"
        _space = f"{settings.PACKAGINATOR_SEARCH_PREFIX} {q}"
        _underscore = f"{settings.PACKAGINATOR_SEARCH_PREFIX}_{q}"
        if True:
            packages = Package.objects.filter(
                Q(title__istartswith=q)
                | Q(title__istartswith=_dash)
                | Q(title__istartswith=_space)
                | Q(title__istartswith=_underscore)
            )
        else:
            query = (
                SearchQuery(q)
                | SearchQuery(_dash)
                | SearchQuery(f"'{_space}'")
                | SearchQuery(_underscore)
            )
            vector = SearchRank("title")
            packages = Package.objects.annotate(
                rank=SearchRank(vector, query)
            ).order_by("-rank")

    packages_already_added_list = []
    grid_slug = request.GET.get("grid", "")
    if packages and grid_slug:
        # if grids := Grid.objects.annotate(search=SearchVector("grid_slug")).search(
        #     search=grid_slug
        # ):
        if grids := Grid.objects.filter(slug=grid_slug):
            grid = grids.first()
            packages_already_added_list = [
                x["slug"] for x in grid.packages.all().only("slug").values("slug")
            ]
            new_packages = tuple(
                packages.exclude(slug__in=packages_already_added_list)
            )[:20]
            number_of_packages = len(new_packages)
            if number_of_packages < 20:
                try:
                    old_packages = packages.filter(
                        slug__in=packages_already_added_list
                    )[: 20 - number_of_packages]
                except AssertionError:
                    old_packages = None

                if old_packages:
                    old_packages = tuple(old_packages)
                    packages = new_packages + old_packages
            else:
                packages = new_packages

    return render(
        request,
        template_name,
        {
            "packages": packages,
            "packages_already_added_list": packages_already_added_list,
        },
    )


@login_required
def usage(request, slug, action):
    success = False
    package = get_object_or_404(Package, slug=slug)

    # Update the current user's usage of the given package as specified by the
    # request.
    if package.usage.filter(username=request.user.username):
        if action.lower() == "add":
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
        if action.lower() == "lower":
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
        package.grid_clear_detail_template_cache()

    # Return an ajax-appropriate response if necessary
    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        response = {"success": success}
        if success:
            response["change"] = change

        return HttpResponse(json.dumps(response))

    # Intelligently determine the URL to redirect the user to based on the
    # available information.
    next = (
        request.GET.get("next")
        or request.headers.get("Referer")
        or reverse("package", kwargs={"slug": package.slug})
    )
    return HttpResponseRedirect(next)


class PackagePython3ListView(SingleTableView):
    table_class = PackageTable
    template_name = "package/python3_list.html"

    def get_queryset(self):
        return (
            Package.objects.filter(version__supports_python3=True)
            .select_related()
            .distinct()
            .order_by("-pypi_downloads", "-repo_watchers", "title")
        )


class PackageListView(TemplateView):
    template_name = "package/package_list.html"

    def get_context_data(self, **kwargs):
        categories = []
        for category in Category.objects.annotate(package_count=Count("package")):
            package_table = PackageByCategoryTable(
                Package.objects.active()
                .filter(category=category)
                .active()
                .select_related()
                .annotate(usage_count=Count("usage"))
                .order_by("-pypi_downloads", "-repo_watchers", "title")[:9],
                prefix=f"{category.slug}_",
                exclude=["last_released"],
            )
            element = {
                "count": category.package_count,
                "description": category.description,
                "slug": category.slug,
                "table": package_table,
                "title": category.title,
                "title_plural": category.title_plural,
            }
            categories.append(element)

        context_data = super().get_context_data(**kwargs)
        context_data["categories"] = categories
        context_data["dpotw"] = Dpotw.objects.get_current()
        context_data["gotw"] = Gotw.objects.get_current()
        return context_data


def package_detail(request, slug, template_name="package/package.html"):
    package = get_object_or_404(
        Package.objects.select_related("category").prefetch_related("grid_set"),
        slug=slug,
    )
    no_development = package.no_development
    try:
        if package.category == Category.objects.get(slug="projects"):
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

    if request.GET.get("message"):
        messages.add_message(request, messages.INFO, request.GET.get("message"))

    return render(
        request,
        template_name,
        dict(
            package=package,
            pypi_ancient=pypi_ancient,
            no_development=no_development,
            pypi_no_release=pypi_no_release,
            warnings=warnings,
            latest_version=package.last_released(),
            repo=package.repo,
        ),
    )


def package_opengraph_detail(request, slug, template_name="package/package_opengraph.html"):
    return package_detail(request, slug, template_name=template_name)


def int_or_0(value):
    try:
        return int(value)
    except ValueError:
        return 0


@login_required
def post_data(request, slug):
    # if request.method == "POST":
    # try:
    #     # TODO Do this this with a form, really. Duh!
    #     package.repo_watchers = int_or_0(request.POST.get("repo_watchers"))
    #     package.repo_forks = int_or_0(request.POST.get("repo_forks"))
    #     package.repo_description = request.POST.get("repo_description")
    #     package.participants = request.POST.get('contributors')
    #     package.fetch_commits()  # also saves
    # except Exception as e:
    #     print e
    package = get_object_or_404(Package, slug=slug)
    package.fetch_pypi_data()
    package.repo.fetch_metadata(package)
    package.repo.fetch_commits(package)
    package.last_fetched = timezone.now()
    package.save()
    return HttpResponseRedirect(reverse("package", kwargs={"slug": package.slug}))


@login_required
def edit_documentation(request, slug, template_name="package/documentation_form.html"):
    package = get_object_or_404(Package, slug=slug)
    form = DocumentationForm(request.POST or None, instance=package)
    if form.is_valid():
        form.save()
        messages.add_message(
            request, messages.INFO, "Package documentation updated successfully"
        )
        return redirect(package)
    return render(request, template_name, dict(package=package, form=form))


@csrf_exempt
def github_webhook(request):
    if request.method == "POST":
        data = json.loads(request.POST["payload"])

        # Webhook Test
        if "zen" in data:
            return HttpResponse(data["hook_id"])

        repo_url = data["repository"]["url"]

        # service test
        if repo_url == "http://github.com/mojombo/grit":
            return HttpResponse("Service Test pass")

        package = get_object_or_404(Package, repo_url=repo_url)
        package.repo.fetch_commits(package)
        package.last_fetched = timezone.now()
        package.save()
    return HttpResponse()
