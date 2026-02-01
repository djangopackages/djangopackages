from functools import cached_property
import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import (
    Count,
    Q,
    Exists,
    OuterRef,
    Subquery,
    IntegerField,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, RedirectView, View
from django.views.generic.edit import CreateView, UpdateView
from django_q.tasks import async_task
from django.utils.translation import gettext_lazy as _

from grid.models import Grid, GridPackage
from package.forms import (
    CategoryPackageFilterForm,
    DocumentationForm,
    FlaggedPackageForm,
    PackageExampleForm,
    PackageCreateForm,
    PackageUpdateForm,
    RepositoryURLForm,
    PackageFilterForm,
)
from package.models import (
    Category,
    FlaggedPackage,
    Package,
    PackageExample,
    RepoHost,
    Version,
)
from searchv2.rules import calc_package_weight
from searchv2.rules import DeprecatedRule
from searchv2.rules import DescriptionRule
from searchv2.rules import DownloadsRule
from searchv2.rules import ForkRule
from searchv2.rules import LastUpdatedRule
from searchv2.rules import RecentReleaseRule
from searchv2.rules import ScoreRuleGroup
from searchv2.rules import UsageCountRule
from searchv2.rules import WatchersRule
from favorites.models import Favorite


class AddPackageView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Package
    form_class = PackageCreateForm
    template_name = "package/add_package.html"

    def test_func(self):
        return self.request.user.profile.can_add_package

    @cached_property
    def grid(self):
        grid_slug = self.request.GET.get("grid_slug")
        if grid_slug:
            try:
                return Grid.objects.get(slug=grid_slug)
            except Grid.DoesNotExist:
                pass
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "repo_form" not in context:
            context["repo_form"] = RepositoryURLForm()
        context["grid"] = self.grid
        context["grid_slug"] = self.request.GET.get("grid_slug")
        return context

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.last_modified_by = self.request.user
        self.object.save()

        if self.grid:
            GridPackage.objects.create(grid=self.grid, package=self.object)

        if not self.grid:
            messages.success(self.request, _("Package added successfully"))
        else:
            messages.success(
                self.request,
                _("Package added successfully to grid: %(grid_title)s")
                % {"grid_title": self.grid.title},
            )

        if self.request.htmx:
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("package", kwargs={"slug": self.object.slug})

    def form_invalid(self, form):
        if self.request.htmx:
            context = {"form": form}
            context["grid"] = self.grid
            return render(self.request, "partials/package_form.html", context)
        return super().form_invalid(form)


class ValidateRepositoryURLView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.can_add_package

    def post(self, request, *args, **kwargs):
        form = RepositoryURLForm(request.POST)
        if form.is_valid():
            repo_url = form.cleaned_data["repo_url"]

            # Check if package exists
            existing_package = Package.objects.filter(repo_url=repo_url).first()
            if existing_package:
                return render(
                    request,
                    "partials/package_exists.html",
                    {"package": existing_package},
                )

            # Pre-fill data
            try:
                parsed = urlparse(repo_url)
                path_parts = parsed.path.strip("/").split("/")
                repo_name = path_parts[-1]

                initial_data = {
                    "repo_url": repo_url,
                    "title": repo_name,
                    "slug": slugify(repo_name),
                    "pypi_url": repo_name,
                }

                domain = parsed.netloc
                initial_data["repo_host"] = RepoHost.from_url(domain)

                package_form = PackageCreateForm(initial=initial_data)
                context = {"form": package_form}
                if "grid_slug" in request.GET:
                    context["grid_slug"] = request.GET["grid_slug"]
                return render(
                    request,
                    "partials/package_form.html",
                    context,
                )
            except Exception:
                pass

        return render(request, "partials/repo_url_form.html", {"repo_form": form})


class PackageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Package
    form_class = PackageUpdateForm
    template_name = "package/edit_package.html"

    def test_func(self):
        return self.request.user.profile.can_edit_package

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.last_modified_by = self.request.user
        self.object.save()
        messages.success(self.request, _("Package updated successfully"))
        if self.request.htmx:
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "edit"
        return context


class PackageFlagView(LoginRequiredMixin, CreateView):
    model = FlaggedPackage
    form_class = FlaggedPackageForm
    template_name = "package/package_flag_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.package = get_object_or_404(
            Package.objects.annotate(
                _has_approved_flag=Exists(
                    FlaggedPackage.objects.filter(
                        package_id=OuterRef("pk"), approved_flag=True
                    )
                )
            ).exclude(_has_approved_flag=True),
            slug=self.kwargs["slug"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["package"] = self.package
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.package = self.package
        response = super().form_valid(form)
        messages.info(self.request, "Flag submitted for review")
        return response

    def get_success_url(self):
        return reverse("package", kwargs={"slug": self.package.slug})


class PackageFlagApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        flag = get_object_or_404(FlaggedPackage, pk=self.kwargs.get("pk"))
        flag.approve()
        messages.success(request, "Flag approved")
        return redirect("package", slug=flag.package.slug)


class PackageFlagRemoveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        flag = get_object_or_404(FlaggedPackage, pk=self.kwargs.get("pk"))
        flag.delete()
        messages.success(request, "Flag removed")
        return redirect("package", slug=flag.package.slug)


class PackageExampleCreateView(LoginRequiredMixin, CreateView):
    model = PackageExample
    form_class = PackageExampleForm
    template_name = "partials/sites_using_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.package = get_object_or_404(Package, slug=self.kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["package"] = self.package
        context["action"] = "add"
        return context

    def form_valid(self, form):
        form.instance.package = self.package
        form.instance.created_by = self.request.user
        self.object = form.save()
        return render(
            self.request,
            "partials/sites_using_card.html",
            {"package": self.package},
        )


class PackageExampleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PackageExample
    form_class = PackageExampleForm
    template_name = "partials/sites_using_form.html"
    pk_url_kwarg = "id"

    def test_func(self):
        return (
            self.request.user.id == self.object.created_by_id
            or self.request.user.is_superuser
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["package"] = self.object.package
        context["action"] = "edit"
        return context

    def form_valid(self, form):
        self.object = form.save()
        return render(
            self.request,
            "partials/sites_using_card.html",
            {"package": self.object.package},
        )


class PackageExampleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = PackageExample
    pk_url_kwarg = "id"
    template_name = "partials/sites_using_card.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return (
            self.request.user.id == self.object.created_by_id
            or self.request.user.is_superuser
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["package"] = self.object.package
        return context

    def post(self, request, *args, **kwargs):
        package = self.object.package
        self.object.delete()
        return render(
            request,
            "partials/sites_using_card.html",
            {"package": package},
        )


class PackageUsageToggleView(LoginRequiredMixin, View):
    """Toggle a user's usage of a package (add or remove)."""

    def get_package(self):
        return get_object_or_404(Package, slug=self.kwargs["slug"])

    def _is_using(self, package, user) -> bool:
        return package.usage.filter(pk=user.pk).exists()

    def _invalidate_caches(self, package, user) -> None:
        cache.delete(f"sitewide_used_packages_list_{user.pk}")

    def get(self, request, slug, action):
        """Handle GET requests for usage toggle."""
        return self.toggle_usage(request, action)

    def post(self, request, slug, action):
        """Handle POST requests for usage toggle."""
        return self.toggle_usage(request, action)

    def toggle_usage(self, request, action):
        """Core logic to toggle package usage."""
        package = self.get_package()
        user = request.user
        action = action.lower()

        is_currently_using = self._is_using(package, user)
        did_change = False

        is_using = is_currently_using

        if action == "add":
            if not is_currently_using:
                package.usage.add(user)
                did_change = True
                is_using = True
        elif action == "remove":
            if is_currently_using:
                package.usage.remove(user)
                did_change = True
                is_using = False

        # Invalidate caches only if there was a change
        if did_change:
            self._invalidate_caches(package, user)

        # Handle HTMX requests - return updated button partial
        if self.request.htmx:
            mobile = bool(request.GET.get("mobile"))
            return render(
                request,
                "partials/usage_button.html",
                {"package": package, "is_using": is_using, "mobile": mobile},
            )

        # Standard redirect for non-AJAX requests
        next_url = (
            request.GET.get("next")
            or request.headers.get("Referer")
            or reverse("package", kwargs={"slug": package.slug})
        )
        return HttpResponseRedirect(next_url)


class PackageRulesView(DetailView):
    template_name = "package/package_rules.html"
    model = Package
    context_object_name = "package"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Package.objects.select_related(
            "category", "latest_version"
        ).prefetch_related("grid_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.object

        group = ScoreRuleGroup(
            name="Activity Rules",
            description="Rules related to the package's recent activity",
            max_score=40,
            documentation_url=f"{settings.DOCS_URL}/rules/#searchv2.rules.ScoreRuleGroup",
            rules=[LastUpdatedRule(), RecentReleaseRule()],
        )

        rules = [
            DeprecatedRule(),
            DescriptionRule(),
            DownloadsRule(),
            ForkRule(),
            UsageCountRule(),
            WatchersRule(),
            group,
        ]

        package_score = calc_package_weight(
            package=package,
            rules=rules,
            max_score=100,
        )

        context.update(
            dict(
                package_score=package_score,
                latest_version=package.latest_version,
                repo=package.repo,
            )
        )
        return context


class PackageDetailView(DetailView):
    template_name = "package/package_detail.html"
    model = Package
    context_object_name = "package"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        version_count_subquery = (
            Version.objects.filter(package_id=OuterRef("pk"))
            .order_by()
            .values("package_id")
            .annotate(c=Count("id"))
            .values("c")[:1]
        )

        qs = (
            super()
            .get_queryset()
            .select_related("category", "deprecates_package", "latest_version")
            .prefetch_related(
                "grid_set",
                "flags",
            )
            .annotate(
                _has_approved_flag=Exists(
                    FlaggedPackage.objects.filter(
                        package_id=OuterRef("pk"), approved_flag=True
                    )
                ),
                # Avoid JOIN+GROUP BY explosion from version fan-out.
                _version_count=Coalesce(
                    Subquery(version_count_subquery, output_field=IntegerField()), 0
                ),
            )
        )
        if self.request.user.is_authenticated:
            qs = qs.annotate(
                _is_favorited=Exists(
                    Favorite.objects.filter(
                        favorited_by=self.request.user, package_id=OuterRef("pk")
                    )
                )
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "is_favorited": getattr(self.object, "_is_favorited", False),
                "commit_count": self.object.commit_count,
                "version_count": getattr(self.object, "_version_count", 0),
                "has_approved_flag": getattr(self.object, "_has_approved_flag", False),
            }
        )
        return context


class PackageOpenGraphDetailView(DetailView):
    template_name = "package/package_opengraph.html"
    model = Package
    context_object_name = "package"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return super().get_queryset().active()


class PackageFetchDataView(LoginRequiredMixin, RedirectView):
    permanent = False
    pattern_name = "package"

    def get_redirect_url(self, *args, **kwargs):
        package = get_object_or_404(
            Package.objects.only("slug"), slug=self.kwargs.get("slug")
        )
        async_task("package.tasks.fetch_package_data_task", package.slug)
        messages.info(self.request, "Package data is being refreshed")
        kwargs["slug"] = package.slug
        return super().get_redirect_url(*args, **kwargs)


class PackageDocumentationUpdateView(LoginRequiredMixin, UpdateView):
    model = Package
    form_class = DocumentationForm
    template_name = "partials/documentation_form.html"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        return get_object_or_404(Package, slug=self.kwargs.get("slug"))

    def form_valid(self, form):
        self.object = form.save()
        return render(
            self.request,
            "partials/documentation_card.html",
            {"package": self.object},
        )


@method_decorator(csrf_exempt, name="dispatch")
class GitHubWebhookView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST["payload"])

        # Webhook Test
        if "zen" in data:
            return HttpResponse(data["hook_id"])

        repo_url = data["repository"]["url"]

        # service test
        if repo_url == "http://github.com/mojombo/grit":
            return HttpResponse("Service Test pass")

        package = get_object_or_404(Package, repo_url=repo_url)
        package.repo.fetch_metadata(package)
        package.last_fetched = timezone.now()
        package.save()
        return HttpResponse()


class PackageVersionListView(ListView):
    template_name = "partials/releases_table.html"
    context_object_name = "versions"
    paginate_by = 10

    def get_queryset(self):
        return Version.objects.by_version_not_hidden(package__slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["package_slug"] = self.kwargs["slug"]
        return context


class BasePackageListView(ListView):
    model = Package
    paginate_by = 20
    context_object_name = "packages"
    template_name = None  # must be set by subclass

    def get_base_queryset(self):
        return (
            Package.objects.active()
            .select_related("category", "latest_version")
            .annotate(usage_count=Count("usage"))
        )

    def get_filter_form(self):
        """
        Return the filter form instance.
        """
        raise NotImplementedError

    def get_default_filter_data(self):
        """
        Default filter_data dict for the view.
        """
        raise NotImplementedError

    def apply_filters(self, queryset):
        """
        Apply filters to the queryset.
        """
        raise NotImplementedError

    def get_list_url(self):
        raise NotImplementedError

    def get_extra_context(self):
        return {}

    def get_queryset(self):
        queryset = self.get_base_queryset()

        self.form = self.get_filter_form()
        self.filter_data = self.get_default_filter_data()

        if self.form.is_valid():
            self.update_filter_data(self.form.cleaned_data)

        queryset = self.apply_filters(queryset)

        return queryset.order_by(self.filter_data["sort"])

    def update_filter_data(self, cleaned_data):
        """
        Populate filter_data from cleaned_data.
        """
        for key in self.filter_data:
            if cleaned_data.get(key):
                self.filter_data[key] = cleaned_data[key]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_sort": self.filter_data["sort"],
                "search_query": self.filter_data.get("q", ""),
                "form": self.form,
                "list_url": self.get_list_url(),
                **self.get_extra_context(),
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return render(
                self.request,
                "partials/package_list_body.html",
                context,
            )
        return super().render_to_response(context, **response_kwargs)


class PackageListView(BasePackageListView):
    template_name = "package/package_list.html"

    def get_filter_form(self):
        return PackageFilterForm(self.request.GET)

    def get_default_filter_data(self):
        return {
            "category": "all",
            "q": "",
            "sort": "-repo_watchers",
        }

    def apply_filters(self, queryset):
        if self.filter_data["category"] != "all":
            queryset = queryset.filter(category__slug=self.filter_data["category"])

        if self.filter_data["q"]:
            queryset = queryset.filter(
                Q(title__icontains=self.filter_data["q"])
                | Q(repo_description__icontains=self.filter_data["q"])
            )

        return queryset

    def get_list_url(self):
        return reverse("packages")

    def get_extra_context(self):
        return {
            "categories": (
                Category.objects.annotate(
                    package_count=Count(
                        "package",
                        filter=Q(
                            package__date_repo_archived__isnull=True,
                            package__date_deprecated__isnull=True,
                            package__deprecated_by__isnull=True,
                            package__deprecates_package__isnull=True,
                        ),
                    )
                )
                .filter(package_count__gt=0)
                .order_by("-package_count")
            ),
            "total_count": Package.objects.active().count(),
            "current_category": self.filter_data["category"],
        }


class PackageByCategoryListView(BasePackageListView):
    template_name = "package/category_package_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_base_queryset(self):
        return super().get_base_queryset().filter(category=self.category)

    def get_filter_form(self):
        return CategoryPackageFilterForm(self.request.GET)

    def get_default_filter_data(self):
        return {
            "q": "",
            "sort": "-repo_watchers",
        }

    def apply_filters(self, queryset):
        if self.filter_data["q"]:
            queryset = queryset.filter(
                Q(title__icontains=self.filter_data["q"])
                | Q(repo_description__icontains=self.filter_data["q"])
            )
        return queryset

    def get_list_url(self):
        return reverse(
            "category",
            kwargs={"slug": self.category.slug},
        )

    def get_extra_context(self):
        return {
            "category": self.category,
            "current_category": self.category.slug,
        }


class PackageByGridListView(BasePackageListView):
    template_name = "package/grid_package_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.grid = get_object_or_404(Grid, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_base_queryset(self):
        return super().get_base_queryset().filter(gridpackage__grid=self.grid)

    def get_filter_form(self):
        return PackageFilterForm(self.request.GET)

    def get_default_filter_data(self):
        return {
            "category": "all",
            "q": "",
            "sort": "-repo_watchers",
        }

    def apply_filters(self, queryset):
        if self.filter_data["category"] != "all":
            queryset = queryset.filter(category__slug=self.filter_data["category"])

        if self.filter_data["q"]:
            queryset = queryset.filter(
                Q(title__icontains=self.filter_data["q"])
                | Q(repo_description__icontains=self.filter_data["q"])
            )

        return queryset

    def get_list_url(self):
        return reverse(
            "grid_packages",
            kwargs={"slug": self.grid.slug},
        )

    def get_extra_context(self):
        return {
            "grid": self.grid,
            "categories": (
                Category.objects.filter(package__gridpackage__grid=self.grid)
                .annotate(
                    package_count=Count(
                        "package",
                        filter=Q(
                            package__date_repo_archived__isnull=True,
                            package__date_deprecated__isnull=True,
                            package__deprecated_by__isnull=True,
                            package__deprecates_package__isnull=True,
                        ),
                    )
                )
                .filter(package_count__gt=0)
                .order_by("-package_count")
            ),
            "total_count": self.grid.packages.filter(
                date_repo_archived__isnull=True,
                date_deprecated__isnull=True,
                deprecated_by__isnull=True,
                deprecates_package__isnull=True,
            ).count(),
            "current_category": self.filter_data["category"],
        }


class MostLikedPackageListView(ListView):
    template_name = "package/package_archive.html"
    model = Package
    paginate_by = 50
    context_object_name = "packages"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("category")
            .annotate(distinct_favs=Count("favorite__favorited_by", distinct=True))
            .filter(distinct_favs__gt=0)
            .order_by("-distinct_favs")
        )

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "title": _("Most Liked Packages"),
                "heading": _("Most liked 50 packages"),
            }
        )
        return context


class LatestPackageListView(ListView):
    template_name = "package/package_archive.html"
    model = Package
    paginate_by = 50
    context_object_name = "packages"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .active()
            .select_related("category")
            .order_by("-created")
        )

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "title": _("Latest Packages"),
                "heading": _("Latest 50 packages added"),
            }
        )
        return context
