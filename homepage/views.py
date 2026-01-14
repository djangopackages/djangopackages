from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from grid.models import Grid
from package.models import Category, Commit, Package, Version
from products.models import Product, Release


class OpenView(TemplateView):
    template_name = "homepage/open.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        classifiers = {
            "total_django_2_2": "Framework :: Django :: 2.2",
            "total_django_3_0": "Framework :: Django :: 3.0",
            "total_django_3_1": "Framework :: Django :: 3.1",
            "total_django_3_2": "Framework :: Django :: 3.2",
            "total_django_4_0": "Framework :: Django :: 4.0",
            "total_django_4_1": "Framework :: Django :: 4.1",
            "total_django_4_2": "Framework :: Django :: 4.2",
            "total_django_5_0": "Framework :: Django :: 5.0",
            "total_django_5_1": "Framework :: Django :: 5.1",
            "total_django_5_2": "Framework :: Django :: 5.2",
            "total_django_6_0": "Framework :: Django :: 6.0",
            "total_python_2_7": "Programming Language :: Python :: 2.7",
            "total_python_3": "Programming Language :: Python :: 3",
            "total_python_3_6": "Programming Language :: Python :: 3.6",
            "total_python_3_7": "Programming Language :: Python :: 3.7",
            "total_python_3_8": "Programming Language :: Python :: 3.8",
            "total_python_3_9": "Programming Language :: Python :: 3.9",
            "total_python_3_10": "Programming Language :: Python :: 3.10",
            "total_python_3_11": "Programming Language :: Python :: 3.11",
            "total_python_3_12": "Programming Language :: Python :: 3.12",
            "total_python_3_13": "Programming Language :: Python :: 3.13",
            "total_python_3_14": "Programming Language :: Python :: 3.14",
            "total_python_3_15": "Programming Language :: Python :: 3.15",
        }
        vcs_providers = {
            "repos_bitbucket": "bitbucket.org",
            "repos_github": "github.com",
            "repos_gitlab": "gitlab.com",
        }

        active_package_aggregations = Package.objects.active().aggregate(
            # Total package count for each VCS provider
            **{
                key: Count("pk", filter=Q(repo_url__contains=value))
                for key, value in vcs_providers.items()
            },
            # Total package count for each classifier
            **{
                key: Count("pk", filter=Q(pypi_classifiers__contains=[value]))
                for key, value in classifiers.items()
            },
        )
        context_data.update(active_package_aggregations)

        all_package_aggregations = Package.objects.aggregate(
            # Total package Count
            total_packages=Count("pk"),
            # Total archived package Count
            archive_packages=Count("pk", filter=~Q(date_repo_archived__isnull=True)),
            # Total deprecated package Count
            deprecated_packages=Count(
                "pk",
                filter=~Q(date_deprecated__isnull=True, deprecated_by__isnull=True),
            ),
        )
        context_data.update(all_package_aggregations)

        context_data["categories"] = Package.objects.active().aggregate(
            **{
                title: Count("pk", filter=Q(category_id=pk))
                for pk, title in Category.objects.values_list("pk", "slug")
            }
        )

        top_grid_list = (
            Grid.objects.all()
            .annotate(num_packages=Count("packages"))
            .filter(num_packages__gte=25)
            .order_by("-num_packages")[0:100]
        )
        top_user_list = (
            User.objects.all()
            .annotate(num_packages=Count("creator"))
            .filter(num_packages__gt=10)
            .order_by("-num_packages")
        )

        context_data.update(
            {
                "top_grid_list": top_grid_list[0:100],
                "top_user_list": top_user_list[0:100],
                "total_categories": Category.objects.count(),
                "total_commits": Commit.objects.count(),
                "total_grids": Grid.objects.count(),
                "total_users": User.objects.count(),
                "total_versions": Version.objects.count(),
            }
        )

        return context_data


class ReadinessView(TemplateView):
    template_name = "homepage/readiness_index.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        # Django Releases
        django_releases = (
            Release.objects.filter(product__slug="django")
            .select_related("product")
            .order_by("-release")
        )
        context_data["django_releases"] = django_releases

        # Python Releases
        python_releases = (
            Release.objects.filter(product__slug="python")
            .select_related("product")
            .order_by("-release")
        )
        context_data["python_releases"] = python_releases

        # Wagtail Releases
        wagtail_releases = (
            Release.objects.filter(product__slug="wagtail")
            .select_related("product")
            .order_by("-release")
        )
        context_data["wagtail_releases"] = wagtail_releases

        return context_data


class ReadinessDetailView(TemplateView):
    template_name = "homepage/readiness_detail.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        limit = 120
        context_data["limit"] = limit

        product_slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=product_slug)
        context_data["product"] = product

        cycle = self.kwargs.get("cycle")
        context_data["cycle"] = cycle

        release = Release.objects.get(product=product, cycle=cycle)
        context_data["release"] = release

        if product_slug == "django":
            pypi_classifier = ["Framework :: Django"]
            ready_condition = f"Framework :: Django :: {cycle}"

        elif product_slug == "python":
            pypi_classifier = [
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
            ]
            ready_condition = f"Programming Language :: Python :: {cycle}"

        elif product_slug == "wagtail":
            pypi_classifier = ["Framework :: Wagtail"]
            ready_condition = f"Framework :: Wagtail :: {cycle}"

        else:
            pypi_classifier = ["None Pizza :: Left Beef"]
            ready_condition = "None Pizza"

        context_data["ready_condition"] = ready_condition

        packages = (
            Package.objects.only(
                "title", "pypi_downloads", "pypi_classifiers", "slug", "repo_watchers"
            )
            .filter(pypi_classifiers__contains=pypi_classifier)
            .exclude(
                Q(title="django") | Q(slug="django")
            )  # TODO: might be worth re-addressing...
            .order_by("-repo_watchers", "-pypi_downloads")[:limit]
        )

        packages = [package.__dict__ for package in packages]
        for package in packages:
            classifiers = [
                classifier
                for classifier in package["pypi_classifiers"]
                if classifier.startswith(pypi_classifier[0])
            ]

            if ready_condition in classifiers:
                package["is_ready"] = "yes"

            elif len(classifiers) > 1:
                package["is_ready"] = "no"

            else:
                package["is_ready"] = "maybe"

        context_data["cycle"] = cycle
        context_data["packages"] = packages
        context_data["product_slug"] = product_slug.title()

        return context_data


class HomepageView(TemplateView):
    template_name = "homepage/index.html"

    def _get_categories(self):
        if not (categories := cache.get("categories")):
            categories = list(
                Category.objects.only(
                    "pk", "slug", "description", "title", "title_plural"
                )
                .annotate(package_count=Count("package"))
                .order_by("-package_count")[:4]
            )
            # cache dict for 5 minutes...
            cache.set("categories", categories, timeout=60 * 5)
        return categories

    def _get_grid_lists(self):
        if not (grids := cache.get("grid_list")):
            grids = list(
                Grid.objects.filter(header=True)
                .only("pk", "slug", "description", "title")
                .annotate(gridpackage_count=Count("gridpackage"))
                .filter(gridpackage_count__gt=2)
                .order_by("title")
            )
            # cache dict for 5 minutes...
            cache.set("grid_list", grids, timeout=60 * 5)

        midpoint = len(grids) // 2 + (len(grids) % 2)
        grids_1 = grids[:midpoint]
        grids_2 = grids[midpoint:]
        return grids_1, grids_2

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = self._get_categories()
        grids_1, grids_2 = self._get_grid_lists()

        # Prefetch versions to avoid N+1 queries when accessing pypi_version
        versions_prefetch = Prefetch(
            "version_set",
            queryset=Version.objects.only("package_id", "number"),
            to_attr="_prefetched_versions",
        )

        # Get the random packages
        random_packages = (
            Package.objects.active()
            .exclude(repo_description__in=[None, ""])
            .prefetch_related(versions_prefetch)
            .order_by("?")
        )

        # Latest Django Packages blog post on homepage
        latest_packages = (
            Package.objects.active()
            .select_related("category")
            .prefetch_related(versions_prefetch)
            .annotate(usage_count=Count("usage"))
            .order_by("-created")
        )
        latest_releases = (
            Package.objects.active()
            .exclude(repo_description__in=[None, ""])
            .prefetch_related(versions_prefetch)
            .distinct()
            .order_by("-version__created")
        )
        most_liked_packages = (
            Package.objects.active()
            .prefetch_related(versions_prefetch)
            .annotate(distinct_favs=Count("favorite__favorited_by", distinct=True))
            .filter(distinct_favs__gt=0)
            .order_by("-distinct_favs")
        )

        context.update(
            {
                "categories": categories,
                "grids_1": grids_1,
                "grids_2": grids_2,
                "latest_packages": latest_packages,
                "latest_releases": latest_releases,
                "random_packages": random_packages,
                "most_liked_packages": most_liked_packages,
            }
        )
        return context


def error_404_view(request, exception=None):
    response = render(request, "404.html")
    response.status_code = 404
    return response


def error_403_view(request, exception=None):
    response = render(request, "403.html")
    response.status_code = 403
    return response


def error_500_view(request):
    try:
        response = render(request, "500.html")
    except Exception:
        response = HttpResponse(
            """<html><body><p>If this seems like a bug, would you please do us a favor and <a href="https://github.com/djangopackages/djangopackages/issues">create a ticket?</a></p></body></html>"""
        )
    response.status_code = 500
    return response


def error_503_view(request):
    response = render(request, "503.html")
    response.status_code = 503
    return response
