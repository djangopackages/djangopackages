"""views for the :mod:`grid` app"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Max, Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils.translation import gettext_lazy as _

from grid.forms import (
    ElementForm,
    FeatureForm,
    GridForm,
    GridPackageFilterForm,
    GridFilterForm,
    GridPackageForm,
)
from grid.models import Element, Feature, Grid, GridPackage
from package.forms import PackageForm
from package.models import Package
from package.views import repo_data_for_js


def build_element_map(elements):
    # Horrifying two-level dict due to needing to use hash() function later
    element_map = {}
    for element in elements:
        element_map.setdefault(element.feature_id, {})
        element_map[element.feature_id][element.grid_package_id] = element
    return element_map


class GridListView(ListView):
    model = Grid
    template_name = "new/grid_list.html"
    paginate_by = 20
    context_object_name = "grids"

    def get_queryset(self):
        queryset = (
            Grid.objects.filter()
            .annotate(
                # `distinct=True` parameter is required here for multiple annotations to not yield the wrong results
                # See: https://docs.djangoproject.com/en/4.2/topics/db/aggregation/#combining-multiple-aggregations
                gridpackage_count=Count("gridpackage", distinct=True),
                active_gridpackage_count=Count(
                    "gridpackage",
                    filter=Q(
                        gridpackage__package__score__gte=max(
                            0, settings.PACKAGE_SCORE_MIN
                        )
                    ),
                    distinct=True,
                ),
                feature_count=Count("feature", distinct=True),
            )
            .filter(gridpackage_count__gt=0)
        )

        self.form = GridFilterForm(self.request.GET)

        self.filter_data = {
            "q": "",
            "sort": "-modified",
        }

        if self.form.is_valid():
            cleaned = self.form.cleaned_data
            if cleaned.get("q"):
                self.filter_data["q"] = cleaned["q"]
            if cleaned.get("sort"):
                self.filter_data["sort"] = cleaned["sort"]

        if self.filter_data["q"]:
            queryset = queryset.filter(
                Q(title__icontains=self.filter_data["q"])
                | Q(description__icontains=self.filter_data["q"])
            )

        return queryset.order_by(self.filter_data["sort"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "current_sort": self.filter_data["sort"],
                "search_query": self.filter_data["q"],
                "form": self.form,
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return render(self.request, "new/partials/grid_list_body.html", context)
        return super().render_to_response(context, **response_kwargs)


class AddGridView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = GridForm
    template_name = "new/add_grid.html"

    def test_func(self):
        return self.request.user.profile.can_add_grid

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.slug})

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.SUCCESS, _("Grid created successfully")
        )
        return super().form_valid(form)


class EditGridView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Grid
    form_class = GridForm
    template_name = "new/add_grid.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def test_func(self):
        return self.request.user.profile.can_edit_grid

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.slug})

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _("Grid has been edited"))
        return super().form_valid(form)


@login_required
def add_feature(request, grid_slug, template_name="grid/update_feature.html"):
    """Adds a feature to the grid, accepts GET and POST requests.

    Requires user to be logged in

    Template context:

    * ``form`` - instance of :class:`grid.forms.FeatureForm` form
    * ``grid`` - instance of :class:`grid.models.Grid` model
    """

    if not request.user.profile.can_add_grid_feature:
        return HttpResponseForbidden("permission denied")

    grid = get_object_or_404(Grid, slug=grid_slug)
    form = FeatureForm(request.POST or None)

    if form.is_valid():
        feature = form.save(commit=False)
        feature.grid = grid
        feature.save()
        return HttpResponseRedirect(reverse("grid", kwargs={"slug": feature.grid.slug}))

    return render(request, template_name, {"form": form, "grid": grid})


@login_required
def edit_feature(request, id, template_name="grid/update_feature.html"):
    """edits feature on a grid - this view has the same
    semantics as :func:`grid.views.add_feature`.

    Requires the user to be logged in.
    """

    if not request.user.profile.can_edit_grid_feature:
        return HttpResponseForbidden("permission denied")

    feature = get_object_or_404(Feature, id=id)
    form = FeatureForm(request.POST or None, instance=feature)

    if form.is_valid():
        feature = form.save()
        return HttpResponseRedirect(reverse("grid", kwargs={"slug": feature.grid.slug}))

    return render(request, template_name, {"form": form, "grid": feature.grid})


@permission_required("grid.delete_feature")
def delete_feature(request, id, template_name="grid/edit_feature.html"):
    # do not need to check permission via profile because
    # we default to being strict about deleting
    """deletes a feature from the grid, ``id`` is id of the
    :class:`grid.models.Feature` model that is to be deleted

    Requires permission `grid.delete_feature`.

    Redirects to the parent :func:`grid.views.grid_detail`
    """

    feature = get_object_or_404(Feature, id=id)
    Element.objects.filter(feature=feature).delete()
    feature.delete()

    return HttpResponseRedirect(reverse("grid", kwargs={"slug": feature.grid.slug}))


@permission_required("grid.delete_gridpackage")
def delete_grid_package(request, id, template_name="grid/edit_feature.html"):
    """Deletes package from the grid, ``id`` is the id of the
    :class:`grid.models.GridPackage` instance

    Requires permission ``grid.delete_gridpackage``.

    Redirects to :func:`grid.views.grid_detail`.
    """

    # do not need to check permission via profile because
    # we default to being strict about deleting
    grid_package = get_object_or_404(GridPackage, id=id)
    grid_package.grid.clear_detail_template_cache()
    Element.objects.filter(grid_package=grid_package).delete()
    grid_package.delete()

    return HttpResponseRedirect(
        reverse("grid", kwargs={"slug": grid_package.grid.slug})
    )


@login_required
def edit_element(
    request, feature_id, package_id, template_name="grid/edit_element.html"
):
    if not request.user.profile.can_edit_grid_element:
        return HttpResponseForbidden("permission denied")

    feature = get_object_or_404(Feature, pk=feature_id)
    grid_package = get_object_or_404(GridPackage, pk=package_id)

    # Sanity check to make sure both the feature and grid_package are related to
    # the same grid!
    if feature.grid_id != grid_package.grid_id:
        raise Http404

    element, created = Element.objects.get_or_create(
        grid_package=grid_package, feature=feature
    )

    form = ElementForm(request.POST or None, instance=element)

    if form.is_valid():
        element = form.save()
        return HttpResponseRedirect(reverse("grid", kwargs={"slug": feature.grid.slug}))

    return render(
        request,
        template_name,
        {
            "form": form,
            "feature": feature,
            "package": grid_package.package,
            "grid": feature.grid,
        },
    )


@login_required
def add_grid_package(request, grid_slug, template_name="grid/add_grid_package.html"):
    """Add an existing package to this grid."""

    if not request.user.profile.can_add_grid_package:
        return HttpResponseForbidden("permission denied")

    grid = get_object_or_404(Grid, slug=grid_slug)
    grid_package = GridPackage()
    form = GridPackageForm(request.POST or None, instance=grid_package)

    if form.is_valid():
        package = get_object_or_404(Package, id=request.POST["package"])
        try:
            GridPackage.objects.get(grid=grid, package=package)
            message = "Sorry, but '%s' is already in this grid." % package.title
            messages.add_message(request, messages.ERROR, message)
        except GridPackage.DoesNotExist:
            grid_package = GridPackage(grid=grid, package=package)
            grid_package.save()
            grid.clear_detail_template_cache()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Package '%s' has been added to the grid '%s'."
                % (package.title, grid.title),
            )
            redirect = request.POST.get("redirect", "")
            if redirect:
                return HttpResponseRedirect(redirect)

            return HttpResponseRedirect(reverse("grid", kwargs={"slug": grid.slug}))

    return render(request, template_name, {"form": form, "grid": grid})


@login_required
def add_new_grid_package(request, grid_slug, template_name="package/package_form.html"):
    """Add a package to a grid that isn't yet represented on the site."""

    if not request.user.profile.can_add_grid_package:
        return HttpResponseForbidden("permission denied")

    grid = get_object_or_404(Grid, slug=grid_slug)

    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)

    if form.is_valid():
        new_package = form.save()
        GridPackage.objects.create(grid=grid, package=new_package)
        return HttpResponseRedirect(reverse("grid", kwargs={"slug": grid_slug}))

    return render(
        request,
        template_name,
        {"form": form, "repo_data": repo_data_for_js(), "action": "add"},
    )


def ajax_grid_list(request, template_name="grid/ajax_grid_list.html"):
    q = request.GET.get("q", "")
    grids = []
    if q:
        grids = Grid.objects.filter(title__istartswith=q)
        package_id = request.GET.get("package_id", "")
        if package_id:
            grids = grids.exclude(gridpackage__package__id=package_id)
    return render(request, template_name, {"grids": grids})


def grid_detail(request, slug, template_name="grid/grid_detail.html"):
    """displays a grid in detail

    Template context:

    * ``grid`` - the grid object
    * ``elements`` - elements of the grid
    * ``features`` - feature set used in the grid
    * ``grid_packages`` - packages involved in the current grid
    * ``filter_form`` - form for filtering the grid packages
    """
    grid = get_object_or_404(Grid, slug=slug)

    # features = grid.feature_set.select_related(None)
    features = Feature.objects.filter(grid=grid)
    grid_packages = grid.grid_packages.select_related(
        "package", "package__category"
    ).filter(package__score__gte=max(0, settings.PACKAGE_SCORE_MIN))

    filter_form = GridPackageFilterForm(request.GET)

    if filter_form.is_valid():
        python3 = filter_form.cleaned_data["python3"]
        stable = filter_form.cleaned_data["stable"]
        sort = filter_form.cleaned_data["sort"]

        if python3:
            grid_packages = grid_packages.filter(
                package__version__supports_python3=python3
            )

        if stable:
            grid_packages = grid_packages.filter(package__version__development_status=5)

        if sort == GridPackageFilterForm.COMMIT_DATE:
            grid_packages = grid_packages.annotate(
                last_commit_date=Max("package__commit__commit_date")
            ).order_by("-last_commit_date")
        elif sort == GridPackageFilterForm.WATCHERS:
            grid_packages = grid_packages.order_by("-package__repo_watchers")
        elif sort == GridPackageFilterForm.FORKS:
            grid_packages = grid_packages.order_by("-package__repo_forks")
        elif sort == GridPackageFilterForm.DOWNLOADS:
            grid_packages = grid_packages.order_by("-package__pypi_downloads")
        else:
            grid_packages = grid_packages.order_by("-package__score")
    else:
        grid_packages = grid_packages.order_by("-package__score")

    elements = Element.objects.filter(
        feature__in=features, grid_package__in=grid_packages
    )

    element_map = build_element_map(elements)

    # These attributes are how we determine what is displayed in the grid
    default_attributes = [
        ("repo_description", "Description"),
        ("category", "Category"),
        ("pypi_downloads", "Downloads"),
        ("last_updated", "Last Updated"),
        ("pypi_version", "Version"),
        ("repo", "Repo"),
        ("commits_over_52", "Commits"),
        ("repo_watchers", "Stars"),
        ("score", "Score"),
        ("repo_forks", "Forks"),
        ("participant_list", "Participants"),
        ("license_latest", "License"),
    ]

    return render(
        request,
        template_name,
        {
            "grid": grid,
            "features": features,
            "grid_packages": grid_packages,
            "attributes": default_attributes,
            "elements": element_map,
            "filter_form": filter_form,
        },
    )


def grid_detail_landscape(
    request, slug, template_name="grid/grid_detail_landscape.html"
):
    """displays a grid in detail

    Template context:

    * ``grid`` - the grid object
    * ``elements`` - elements of the grid
    * ``features`` - feature set used in the grid
    * ``grid_packages`` - packages involved in the current grid
    """

    return grid_detail(request, slug, template_name=template_name)


def grid_opengraph_detail(request, slug, template_name="grid/grid_opengraph.html"):
    return grid_detail(request, slug, template_name=template_name)


class GridListAPIView(ListAPIView):
    model = Grid
    paginate_by = 20


class GridDetailAPIView(RetrieveAPIView):
    model = Grid


def grid_timesheet(request, slug, template_name="grid/grid_timesheet.html"):
    grid = get_object_or_404(Grid, slug=slug)
    grid_packages = grid.grid_packages.order_by("-package__modified").select_related()

    return render(
        request,
        template_name,
        {
            "grid": grid,
            "grid_packages": grid_packages,
        },
    )
