from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from random import sample

from grid.models import Grid
from homepage.models import Dpotw, Gotw, PSA
from package.models import Category, Commit, Package, Version


class OpenView(TemplateView):
    template_name = "pages/open.html"

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
            "total_python_2_7": "Programming Language :: Python :: 2.7",
            "total_python_3": "Programming Language :: Python :: 3",
            "total_python_3_6": "Programming Language :: Python :: 3.6",
            "total_python_3_7": "Programming Language :: Python :: 3.7",
            "total_python_3_8": "Programming Language :: Python :: 3.8",
            "total_python_3_9": "Programming Language :: Python :: 3.9",
            "total_python_3_10": "Programming Language :: Python :: 3.10",
            "total_python_3_11": "Programming Language :: Python :: 3.11",
        }

        for classifier in classifiers:
            context_data[classifier] = (
                Package.objects.active()
                .filter(pypi_classifiers__contains=[classifiers[classifier]])
                .count()
            )

        categories = Category.objects.all()
        category_data = {}
        for category in categories:
            category_data[category] = (
                Package.objects.active().filter(category=category).count()
            )
        context_data["categories"] = category_data

        top_grid_list = (
            Grid.objects.all()
            .annotate(num_packages=Count("packages"))
            .filter(num_packages__gt=15)
            .order_by("-num_packages")[0:100]
        )
        top_user_list = (
            User.objects.all()
            .annotate(num_packages=Count("creator"))
            .filter(num_packages__gt=10)
            .order_by("-num_packages")
        )

        repos_bitbucket = (
            Package.objects.active().filter(repo_url__contains="bitbucket.org").count()
        )
        repos_github = (
            Package.objects.active().filter(repo_url__contains="github.com").count()
        )
        repos_gitlab = (
            Package.objects.active().filter(repo_url__contains="gitlab.com").count()
        )

        archive_packages = Package.objects.exclude(date_repo_archived__isnull=True)
        deprecated_packages = Package.objects.exclude(
            Q(date_deprecated__isnull=True), Q(deprecated_by__isnull=True)
        )

        context_data.update(
            {
                "archive_packages": archive_packages.count(),
                "deprecated_packages": deprecated_packages.count(),
                "repos_bitbucket": repos_bitbucket,
                "repos_github": repos_github,
                "repos_gitlab": repos_gitlab,
                "top_grid_list": top_grid_list[0:100],
                "top_user_list": top_user_list[0:100],
                "total_categories": Category.objects.count(),
                "total_commits": Commit.objects.count(),
                "total_grids": Grid.objects.count(),
                "total_packages": Package.objects.count(),
                "total_users": User.objects.count(),
                "total_versions": Version.objects.count(),
            }
        )

        return context_data


class SitemapView(TemplateView):

    template_name = "sitemap.xml"
    content_type = "text/xml"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["packages"] = Package.objects.all()
        data["grids"] = Grid.objects.all()
        return data


def homepage(request, template_name="homepage.html"):
    if cache.get("categories"):
        categories = cache.get("categories")
    else:
        categories = list(
            Category.objects.only(
                "pk", "slug", "description", "title", "title_plural"
            ).annotate(package_count=Count("package"))
        )
        # cache dict for 5 minutes...
        cache.set("categories", categories, timeout=60 * 5)

    # get up to 5 random packages
    package_list = Package.objects.active().values_list("pk", flat=True)
    package_count = package_list.count()
    random_packages = []
    if package_list.exists():
        package_ids = set()

        # Get 5 random keys
        package_ids = sample(
            list(
                range(1, package_count + 1)
            ),  # generate a list from 1 to package_count +1
            min(
                package_count, 10
            ),  # Get a sample of the smaller of 10 or the package count
        )

        # Get the random packages
        random_packages = Package.objects.filter(pk__in=package_ids)[:5]

    try:
        potw = Dpotw.objects.latest().package
    except Dpotw.DoesNotExist:
        potw = None
    except Package.DoesNotExist:
        potw = None

    try:
        gotw = Gotw.objects.latest().grid
    except Gotw.DoesNotExist:
        gotw = None
    except Grid.DoesNotExist:
        gotw = None

    # Public Service Announcement on homepage
    try:
        psa_body = PSA.objects.latest().body_text
    except PSA.DoesNotExist:
        psa_body = '<p>There are currently no announcements.  To request a PSA, tweet at <a href="http://twitter.com/open_comparison">@Open_Comparison</a>.</p>'

    # Latest Django Packages blog post on homepage
    latest_packages = Package.objects.active().order_by("-created")[:5]
    latest_python3 = (
        Version.objects.filter(supports_python3=True)
        .select_related("package")
        .distinct()
        .order_by("-created")[:5]
    )

    return render(
        request,
        template_name,
        {
            "categories": categories,
            "gotw": gotw,
            "latest_packages": latest_packages,
            "latest_python3": latest_python3,
            "package_count": package_count,
            "potw": potw,
            "psa_body": psa_body,
            "random_packages": random_packages,
            # "": Package.objects.active()
            # .filter(version__supports_python3=True)
            # .select_related()
            # .distinct()
            # .count(),
        },
    )


def error_404_view(request):
    response = render(request, "404.html")
    response.status_code = 404
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


def health_check_view(request):
    return HttpResponse("ok")
