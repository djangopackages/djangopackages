from functools import cached_property
from typing import Any
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)

from django.db.models import (
    Count,
    Max,
    Q,
    OuterRef,
    Subquery,
    IntegerField,
    BooleanField,
)
from django.db.models.functions import Coalesce
from django.db.models.query import Prefetch
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, DeleteView
from django.views.generic.edit import UpdateView
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme

from core.utils import PackageStatus
from grid.cache import GRID_DETAIL_PAYLOAD_TIMEOUT, get_grid_detail_payload_cache_key

from grid.forms import (
    ElementForm,
    FeatureForm,
    GridForm,
    GridDetailFilterForm,
    GridFilterForm,
    GridPackageForm,
)
from grid.models import Element, Feature, Grid, GridPackage
from package.models import Package

# Commit import disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
from package.models import Version


def build_element_map(elements):
    """Build the two-level mapping used by templates.

    Shape:
        feature_id -> grid_package_id -> {"text": str}
    """
    element_map: dict[int, dict[int, dict[str, Any]]] = {}
    for element in elements:
        element_map.setdefault(element.feature_id, {})
        element_map[element.feature_id][element.grid_package_id] = {
            "text": element.text,
        }
    return element_map


class GridDetailView(DetailView):
    model = Grid
    template_name = "grid/grid_detail.html"
    context_object_name = "grid"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    max_packages = 8

    def get_filter_data(self):
        """Get filter parameters from the form"""
        self.filter_form = GridDetailFilterForm(self.request.GET)
        filter_data = {
            "python3": False,
            "stable": False,
            "sort": GridDetailFilterForm.SCORE,
            "q": "",
        }

        if self.filter_form.is_valid():
            cleaned = self.filter_form.cleaned_data
            filter_data["python3"] = cleaned.get("python3", False)
            filter_data["stable"] = cleaned.get("stable", False)
            filter_data["sort"] = cleaned.get("sort") or GridDetailFilterForm.SCORE
            filter_data["q"] = cleaned.get("q", "")

        return filter_data

    def _get_payload_cache_key(self, *, grid: Grid, filter_data: dict[str, Any]) -> str:
        return get_grid_detail_payload_cache_key(
            grid_id=grid.pk,
            language=get_language(),
            filter_data=filter_data,
            max_packages=self.max_packages,
        )

    def get_grid_packages(self, grid: Grid, filter_data: dict[str, Any]):
        """Get filtered and sorted grid packages"""
        # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
        # cutoff = now() - timedelta(weeks=52)
        version_subquery = (
            Version.objects.filter(package_id=OuterRef("package_id"))
            .exclude(upload_time=None)
            .order_by("-upload_time")
            .values("development_status")[:1]
        )

        supports_python3_subquery = (
            Version.objects.filter(package_id=OuterRef("package_id"))
            .exclude(upload_time=None)
            .order_by("-upload_time")
            .values("supports_python3")[:1]
        )

        grid_packages = (
            grid.gridpackage_set.select_related(
                "package",
                "package__category",
            )
            .prefetch_related(
                Prefetch(
                    "package__version_set",
                    queryset=Version.objects.only(
                        "package_id",
                        "number",
                        "upload_time",
                        "license",
                        "licenses",
                        "development_status",
                        "supports_python3",
                    ).order_by("-upload_time"),
                    to_attr="_prefetched_versions",
                ),
                # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
                # Prefetch(
                #     "package__commit_set",
                #     queryset=Commit.objects.filter(commit_date__gt=cutoff)
                #     .only("package_id", "commit_date")
                #     .order_by("-commit_date"),
                #     to_attr="_prefetched_commits_52w",
                # ),
                "package__usage",
            )
            .filter(package__score__gte=max(0, settings.PACKAGE_SCORE_MIN))
            .annotate(usage_count=Count("package__usage", distinct=True))
            .annotate(last_commit_date=Max("package__commit__commit_date"))
            .annotate(
                development_status=Coalesce(
                    Subquery(version_subquery, output_field=IntegerField()), 0
                )
            )
            .annotate(
                supports_python3_latest=Coalesce(
                    Subquery(supports_python3_subquery, output_field=BooleanField()),
                    # Python 2 has been EOL for a long time; default to True
                    True,
                )
            )
        )

        # Apply search filter
        if filter_data["q"]:
            grid_packages = grid_packages.filter(
                Q(package__title__icontains=filter_data["q"])
                | Q(package__repo_description__icontains=filter_data["q"])
            )

        # Apply Python 3 filter
        if filter_data["python3"]:
            grid_packages = grid_packages.filter(supports_python3_latest=True)

        # Apply stable filter
        if filter_data["stable"]:
            grid_packages = grid_packages.filter(
                development_status=PackageStatus.STABLE
            )

        # Apply sorting
        sort = filter_data["sort"]
        if sort == GridDetailFilterForm.COMMIT_DATE:
            grid_packages = grid_packages.order_by("-last_commit_date")
        elif sort == GridDetailFilterForm.WATCHERS:
            grid_packages = grid_packages.order_by("-package__repo_watchers")
        elif sort == GridDetailFilterForm.FORKS:
            grid_packages = grid_packages.order_by("-package__repo_forks")
        elif sort == GridDetailFilterForm.DOWNLOADS:
            grid_packages = grid_packages.order_by("-package__pypi_downloads")
        elif sort == GridDetailFilterForm.TITLE:
            grid_packages = grid_packages.order_by("package__title")
        else:
            grid_packages = grid_packages.order_by("-package__score")

        return grid_packages

    def _get_total_package_count(self, grid: Grid) -> int:
        # Total count is for the whole grid (not filter-dependent)
        return grid.gridpackage_set.count()

    def _limit_grid_packages(self, grid_packages_qs, total_package_count: int):
        has_more_packages = total_package_count > self.max_packages
        grid_packages = list(grid_packages_qs[: self.max_packages])
        return grid_packages, has_more_packages

    def _populate_derived_package_fields(self, grid_packages) -> None:
        """Attach a few derived values used by templates.

        These are intentionally computed before serialization so templates can
        access them directly on `grid_package`.
        """
        for grid_package in grid_packages:
            package = grid_package.package
            grid_package.pypi_version = package.pypi_version()
            grid_package.license_latest = package.license_latest
            # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
            # grid_package.commits_over_52 = package.commits_over_52()

    def _get_features(self, grid: Grid):
        return list(Feature.objects.filter(grid=grid).order_by("pk"))

    def _get_elements(self, *, features, grid_packages):
        return Element.objects.filter(
            feature__in=features, grid_package__in=grid_packages
        ).select_related("feature", "grid_package")

    def _serialize_grid_packages(self, grid_packages):
        payload_grid_packages: list[dict[str, Any]] = []
        for grid_package in grid_packages:
            package = grid_package.package
            category = package.category
            payload_grid_packages.append(
                {
                    "id": grid_package.pk,
                    "pk": grid_package.pk,
                    "usage_count": grid_package.usage_count,
                    "development_status": grid_package.development_status,
                    "last_commit_date": grid_package.last_commit_date,
                    "pypi_version": grid_package.pypi_version,
                    "license_latest": grid_package.license_latest,
                    # Disabled for performance - see https://github.com/djangopackages/djangopackages/issues/1498
                    # "commits_over_52": grid_package.commits_over_52,
                    "package": {
                        "id": package.pk,
                        "pk": package.pk,
                        "slug": package.slug,
                        "title": package.title,
                        "repo_description": package.repo_description,
                        "repo_url": package.repo_url,
                        "pypi_url": package.pypi_url,
                        "documentation_url": package.documentation_url,
                        "supports_python3": package.supports_python3,
                        "repo_watchers": package.repo_watchers,
                        "repo_forks": package.repo_forks,
                        "pypi_downloads": package.pypi_downloads,
                        "score": package.score,
                        "get_absolute_url": package.get_absolute_url(),
                        "category": (
                            {
                                "id": category.pk,
                                "pk": category.pk,
                                "title": category.title,
                                "get_absolute_url": category.get_absolute_url(),
                            }
                            if category
                            else None
                        ),
                    },
                }
            )
        return payload_grid_packages

    def _serialize_features(self, features):
        return [
            {
                "id": feature.pk,
                "pk": feature.pk,
                "title": feature.title,
                "description": feature.description,
            }
            for feature in features
        ]

    def _build_payload(
        self, *, grid: Grid, filter_data: dict[str, Any]
    ) -> dict[str, Any]:
        # Compute the expensive payload once per grid/version/filter.
        grid_packages_qs = self.get_grid_packages(grid, filter_data)

        total_package_count = self._get_total_package_count(grid)
        grid_packages, has_more_packages = self._limit_grid_packages(
            grid_packages_qs, total_package_count
        )
        self._populate_derived_package_fields(grid_packages)

        # Only show features if grid has 8 or fewer active packages (for performance)
        show_features = total_package_count <= self.max_packages

        if show_features:
            features = self._get_features(grid)
            elements = self._get_elements(
                features=features, grid_packages=grid_packages
            )
            element_map = build_element_map(elements)
        else:
            features = []
            element_map = {}

        return {
            "grid_packages": self._serialize_grid_packages(grid_packages),
            "features": self._serialize_features(features),
            "element_map": element_map,
            "total_package_count": total_package_count,
            "has_more_packages": has_more_packages,
            "show_features": show_features,
        }

    def _get_or_build_payload(
        self, *, grid: Grid, filter_data: dict[str, Any]
    ) -> dict[str, Any]:
        cache_key = self._get_payload_cache_key(grid=grid, filter_data=filter_data)
        payload = cache.get(cache_key)

        if payload is None:
            payload = self._build_payload(grid=grid, filter_data=filter_data)
            cache.set(cache_key, payload, GRID_DETAIL_PAYLOAD_TIMEOUT)

        return payload

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grid = self.object

        # Get filter data
        filter_data = self.get_filter_data()

        payload = self._get_or_build_payload(grid=grid, filter_data=filter_data)

        context.update(
            {
                "grid_packages": payload["grid_packages"],
                "features": payload["features"],
                "element_map": payload["element_map"],
                "filter_form": self.filter_form,
                "filter_data": filter_data,
                "total_package_count": payload["total_package_count"],
                "has_more_packages": payload["has_more_packages"],
                "show_features": payload["show_features"],
                "max_packages": self.max_packages,
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return render(self.request, "partials/grid_comparison_table.html", context)
        return super().render_to_response(context, **response_kwargs)


class GridListView(ListView):
    model = Grid
    template_name = "grid/grid_list.html"
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
            return render(self.request, "partials/grid_list_body.html", context)
        return super().render_to_response(context, **response_kwargs)


class AddGridView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = GridForm
    template_name = "grid/add_grid.html"

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
    template_name = "grid/add_grid.html"
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
    template_name = "grid/add_feature.html"

    def dispatch(self, request, *args, **kwargs):
        self.grid = get_object_or_404(Grid, slug=self.kwargs["grid_slug"])
        return super().dispatch(request, *args, **kwargs)

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
    template_name = "grid/add_feature.html"
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
    template_name = "grid/delete_feature.html"
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
    template_name = "grid/delete_grid_package.html"
    pk_url_kwarg = "id"
    permission_required = "grid.delete_gridpackage"

    def get_queryset(self):
        return super().get_queryset().select_related("grid")

    def get_success_url(self):
        return reverse("grid", kwargs={"slug": self.object.grid.slug})

    def delete(self, request, *args, **kwargs):
        messages.add_message(
            self.request, messages.SUCCESS, _("Package removed from grid successfully")
        )
        return super().delete(request, *args, **kwargs)


class EditElementView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Element
    form_class = ElementForm
    template_name = "grid/edit_element.html"

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
    template_name = "grid/add_grid_package.html"

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
        messages.success(
            self.request,
            f"Package '{package.title}' has been added to the grid '{grid.title}'.",
        )
        return super().form_valid(form)


class AjaxPackageSearchView(ListView):
    model = Package
    template_name = "partials/package_search_results.html"
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
    template_name = "partials/grid_search_results.html"
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
    template_name = "grid/grid_timesheet.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grid_packages"] = (
            self.object.gridpackage_set.order_by("-package__modified")
            .select_related("package")
            .annotate(last_commit_date=Max("package__commit__commit_date"))
        )
        return context
