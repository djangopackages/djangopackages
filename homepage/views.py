from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import BooleanField, Count, ExpressionWrapper, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext
from django.views.generic import TemplateView
from reversion.admin import get_object_or_404

from grid.models import Grid
from package.models import Category, Package, RepoHost, Version
from products.models import Product, Release


# The domain that identifies each host, matching RepoHost.from_url. Forgejo
# is self-hosted on any domain, so it can only ever be counted from a
# repo_host someone set by hand.
REPO_HOST_DOMAINS = {
    RepoHost.GITHUB: "github.com",
    RepoHost.GITLAB: "gitlab.com",
    RepoHost.BITBUCKET: "bitbucket.org",
    RepoHost.CODEBERG: "codeberg.org",
    RepoHost.FORGEJO: None,
}

# Enough to tell six slices apart, and readable on both themes.
REPO_HOST_COLORS = {
    RepoHost.GITHUB: "#24292f",
    RepoHost.GITLAB: "#fc6d26",
    RepoHost.BITBUCKET: "#0052cc",
    RepoHost.CODEBERG: "#2185d0",
    RepoHost.FORGEJO: "#d97706",
    "other": "#94a3b8",
}


def repo_host_query(host):
    """Count a host from repo_host when it is set, and from the URL when not.

    repo_host defaults to AUTO_DETECT and is empty for nearly every package,
    so the URL is what does the work. Honouring the field first means an
    admin can correct a package the URL cannot place, a self-hosted Forgejo
    being the case it exists for.
    """
    chosen = Q(repo_host=host)
    domain = REPO_HOST_DOMAINS.get(host)

    if domain is None:
        return chosen

    return chosen | Q(repo_host=RepoHost.AUTO_DETECT, repo_url__icontains=domain)


def repo_host_breakdown():
    """Active packages per repository host, largest first, with percentages.

    Anything the URL cannot place lands in "Other", which is where a
    self-hosted forge shows up until someone sets its repo_host.
    """
    # Labels are forced to str because this goes through json_script.
    hosts = list(REPO_HOST_DOMAINS)

    counts = Package.objects.active().aggregate(
        total=Count("pk"),
        **{host.value: Count("pk", filter=repo_host_query(host)) for host in hosts},
    )

    total = counts.pop("total")

    rows = [
        {
            "slug": host.value,
            "label": str(host.label),
            "count": counts[host.value],
            "color": REPO_HOST_COLORS[host],
        }
        for host in hosts
    ]

    placed = sum(row["count"] for row in rows)
    rows.append(
        {
            "slug": "other",
            "label": gettext("Other"),
            "count": total - placed,
            "color": REPO_HOST_COLORS["other"],
        }
    )

    for row in rows:
        row["percent"] = round(row["count"] / total * 100, 1) if total else 0.0

    # Empty hosts would be a slice of nothing and a row saying 0.0%.
    rows = [row for row in rows if row["count"]]
    rows.sort(key=lambda row: -row["count"])

    return {"rows": rows, "total": total}


class OpenView(TemplateView):
    template_name = "homepage/open.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        classifiers = {
            "total_django_3_0": "Framework :: Django :: 3.0",
            "total_django_3_1": "Framework :: Django :: 3.1",
            "total_django_4_0": "Framework :: Django :: 4.0",
            "total_django_4_1": "Framework :: Django :: 4.1",
            "total_django_4_2": "Framework :: Django :: 4.2",
            "total_django_5_0": "Framework :: Django :: 5.0",
            "total_django_5_1": "Framework :: Django :: 5.1",
            "total_django_5_2": "Framework :: Django :: 5.2",
            "total_django_6_0": "Framework :: Django :: 6.0",
            "total_django_6_1": "Framework :: Django :: 6.1",
            "total_django_6_2": "Framework :: Django :: 6.2",
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
        active_package_aggregations = Package.objects.active().aggregate(
            # Total package count for each classifier
            **{
                key: Count("pk", filter=Q(pypi_classifiers__contains=[value]))
                for key, value in classifiers.items()
            },
        )
        context_data.update(active_package_aggregations)

        context_data["repo_hosts"] = repo_host_breakdown()

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
                slug: Count("pk", filter=Q(category__slug=slug))
                for slug in Category.objects.values_list("slug", flat=True)
            }
        )

        pypi_packages = Package.objects.active().exclude(
            Q(pypi_url="") | Q(pypi_url__isnull=True)
        )
        context_data["pypi_stats"] = pypi_packages.aggregate(
            total_pypi_packages=Count("pk"),
            total_pypi_downloads=Sum("pypi_downloads"),
        )

        top_grid_list = (
            Grid.objects.approved()
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
                "total_grids": Grid.objects.approved().count(),
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
    package_limit = 120

    def _get_product(self):
        product_slug = self.kwargs.get("product_slug")
        return get_object_or_404(Product, slug=product_slug)

    def _get_release(self, product):
        cycle = self.kwargs.get("cycle")
        return get_object_or_404(Release, product=product, cycle=cycle)

    def _get_product_classifiers_and_ready_condition(self, product, release):
        match product.slug:
            case "django":
                pypi_classifier = ["Framework :: Django"]
                ready_condition = f"Framework :: Django :: {release.cycle}"

            case "python":
                pypi_classifier = [
                    "Programming Language :: Python",
                    "Programming Language :: Python :: 3",
                ]
                ready_condition = f"Programming Language :: Python :: {release.cycle}"
            case "wagtail":
                pypi_classifier = ["Framework :: Wagtail"]
                ready_condition = f"Framework :: Wagtail :: {release.cycle}"
            case _:
                pypi_classifier = ["None Pizza :: Left Beef"]
                ready_condition = "None Pizza"
        return pypi_classifier, ready_condition

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        product = self._get_product()
        release = self._get_release(product)

        pypi_classifier, ready_condition = (
            self._get_product_classifiers_and_ready_condition(product, release)
        )

        packages = (
            Package.objects.only(
                "title", "pypi_downloads", "pypi_classifiers", "slug", "repo_watchers"
            )
            .filter(pypi_classifiers__contains=pypi_classifier)
            .exclude(
                Q(title="django") | Q(slug="django")
            )  # TODO: might be worth re-addressing...
            .order_by("-repo_watchers", "-pypi_downloads")[: self.package_limit]
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

        context_data.update(
            {
                "limit": self.package_limit,
                "product": product,
                "release": release,
                "ready_condition": ready_condition,
                "cycle": release.cycle,
                "packages": packages,
                "product_slug": product.slug.title(),
            }
        )

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
                # "Other" is the one nobody is looking for, so it goes last
                # however big it gets, rather than sitting second because it
                # is the catch-all.
                .annotate(
                    is_catch_all=ExpressionWrapper(
                        Q(slug="other"), output_field=BooleanField()
                    )
                )
                .order_by("is_catch_all", "-package_count")
            )
            # cache dict for 5 minutes...
            cache.set("categories", categories, timeout=60 * 5)
        return categories

    def _get_grid_lists(self):
        if not (grids := cache.get("grid_list")):
            grids = list(
                Grid.objects.approved()
                .filter(header=True)
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

        # Get the random packages
        random_packages = (
            Package.objects.active()
            .exclude(repo_description__in=[None, ""])
            .select_related("latest_version")
            .order_by("?")
        )

        # Latest Django Packages blog post on homepage
        latest_packages = (
            Package.objects.active()
            .select_related("category", "latest_version")
            .annotate(usage_count=Count("usage"))
            .order_by("-created")
        )
        latest_releases = (
            Package.objects.active()
            .exclude(repo_description__in=[None, ""])
            .exclude(latest_version__isnull=True)
            .select_related("latest_version")
            .order_by("-latest_version__upload_time")
        )
        most_liked_packages = (
            Package.objects.active()
            .select_related("latest_version")
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
    context = {"exception_message": str(exception) if exception else ""}
    response = render(request, "403.html", context)
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
