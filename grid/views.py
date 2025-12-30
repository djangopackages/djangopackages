"""views for the :mod:`grid` app"""

from functools import cached_property
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)
from django.db.models import Count, Max, Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, DeleteView
from django.views.generic.edit import UpdateView
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme

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


class AddFeatureView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = FeatureForm
    template_name = "new/add_feature.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.grid = get_object_or_404(Grid, slug=self.kwargs["grid_slug"])

    def test_func(self):
        return self.request.user.profile.can_add_grid_feature

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grid"] = self.grid
        return context

    def form_valid(self, form):
        form.instance.grid = self.grid
        messages.add_message(
            self.request, messages.SUCCESS, _("Feature added successfully")
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.grid.slug})


class EditFeatureView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Feature
    form_class = FeatureForm
    template_name = "new/add_feature.html"
    pk_url_kwarg = "id"

    def test_func(self):
        return self.request.user.profile.can_edit_grid_feature

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.grid.slug})

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.SUCCESS, _("Feature updated successfully")
        )
        return super().form_valid(form)


class DeleteFeatureView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Feature
    template_name = "new/delete_feature.html"
    pk_url_kwarg = "id"
    permission_required = "grid.delete_feature"

    def get_queryset(self):
        return super().get_queryset().select_related("grid")

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.grid.slug})

    def delete(self, request, *args, **kwargs):
        messages.add_message(
            self.request, messages.SUCCESS, _("Feature deleted successfully")
        )
        return super().delete(request, *args, **kwargs)


class DeleteGridPackageView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = GridPackage
    template_name = "new/delete_grid_package.html"
    pk_url_kwarg = "id"
    permission_required = "grid.delete_gridpackage"

    def get_queryset(self):
        return super().get_queryset().select_related("grid")

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.grid.slug})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.grid.clear_detail_template_cache()
        messages.add_message(
            self.request, messages.SUCCESS, _("Package removed from grid successfully")
        )
        return super().delete(request, *args, **kwargs)


class EditElementView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Element
    form_class = ElementForm
    template_name = "new/edit_element.html"

    def test_func(self):
        return self.request.user.profile.can_edit_grid_element

    def get_object(self, queryset=None):
        feature_id = self.kwargs.get("feature_id")
        package_id = self.kwargs.get("package_id")

        self.feature = get_object_or_404(Feature, pk=feature_id)
        self.grid_package = get_object_or_404(GridPackage, pk=package_id)

        if self.feature.grid_id != self.grid_package.grid_id:
            raise Http404

        element, _ = Element.objects.get_or_create(
            grid_package=self.grid_package, feature=self.feature
        )
        return element

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature"] = self.feature
        context["package"] = self.grid_package.package
        context["grid"] = self.feature.grid
        return context

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.feature.grid.slug})

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.SUCCESS, _("Element updated successfully")
        )
        return super().form_valid(form)


class AddGridPackageView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = GridPackage
    form_class = GridPackageForm
    template_name = "new/add_grid_package.html"

    @cached_property
    def grid(self):
        return get_object_or_404(Grid, slug=self.kwargs["grid_slug"])

    def test_func(self):
        return bool(self.request.user.profile.can_add_grid_package)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grid"] = self.grid
        return context

    def get_success_url(self):
        # prefer POST 'redirect' then GET 'next'
        redirect = self.request.POST.get("redirect")
        if redirect and url_has_allowed_host_and_scheme(
            url=redirect,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return redirect
        return reverse("grid", kwargs={"slug": self.grid.slug})

    def form_valid(self, form):
        grid = self.grid
        package = form.cleaned_data.get("package")

        if GridPackage.objects.filter(grid=grid, package=package).exists():
            form.add_error(
                "package", f"Package '{package.title}' is already in this grid."
            )
            return self.form_invalid(form)

        form.instance.grid = grid
        # clear cache and inform the user
        grid.clear_detail_template_cache()
        messages.success(
            self.request,
            f"Package '{package.title}' has been added to the grid '{grid.title}'.",
        )
        return super().form_valid(form)


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


class AjaxPackageSearchView(ListView):
    model = Package
    template_name = "new/partials/package_search_results.html"
    context_object_name = "packages"

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        grid_slug = self.request.GET.get("grid", "")

        if not q:
            return Package.objects.none()

        qs = Package.objects.filter(Q(title__icontains=q) | Q(repo_url__icontains=q))

        if grid_slug:
            qs = qs.exclude(gridpackage__grid__slug=grid_slug)

        return qs.select_related("category").order_by("-repo_watchers")[:20]


class AjaxGridSearchView(ListView):
    model = Package
    template_name = "new/partials/grid_search_results.html"
    context_object_name = "grids"

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        package_id = self.request.GET.get("package_id", "")

        if not q:
            return Grid.objects.none()

        qs = Grid.objects.filter(title__icontains=q)

        if package_id:
            qs = qs.exclude(gridpackage__package_id=package_id)

        return qs[:20]


class GridOpenGraphView(DetailView):
    model = Grid
    template_name = "grid/grid_opengraph.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"


class GridTimesheetView(DetailView):
    model = Grid
    template_name = "new/grid_timesheet.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grid_packages"] = self.object.grid_packages.order_by(
            "-package__modified"
        ).select_related()
        return context


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
