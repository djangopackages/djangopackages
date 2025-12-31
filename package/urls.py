from django.urls import path, re_path
from django.views.generic.dates import ArchiveIndexView
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from package.models import Package
from package.views import (
    PackageOpenGraphDetailView,
    PackageExampleCreateView,
    AddPackageView,
    ValidateRepositoryURLView,
    PackageExampleDeleteView,
    PackageDocumentationUpdateView,
    PackageExampleUpdateView,
    PackageUpdateView,
    PackageFlagApproveView,
    PackageFlagView,
    PackageFlagRemoveView,
    GitHubWebhookView,
    PackageRulesView,
    PackageFetchDataView,
    usage,
    PackageVersionListView,
    PackageDetailView,
    PackageListView,
)

urlpatterns = [
    path(
        "",
        view=PackageListView.as_view(),
        name="packages",
    ),
    path(
        "latest/",
        view=ArchiveIndexView.as_view(
            queryset=Package.objects.active().select_related("category"),
            paginate_by=50,
            date_field="created",
            extra_context={
                "title": _("Latest Packages"),
                "heading": _("Latest 50 packages added"),
            },
            template_name="new/package_archive.html",
        ),
        name="latest_packages",
    ),
    path(
        "liked/",
        view=ArchiveIndexView.as_view(
            queryset=Package.objects.active()
            .select_related("category")
            .annotate(distinct_favs=Count("favorite__favorited_by", distinct=True))
            .filter(distinct_favs__gt=0),
            paginate_by=50,
            date_field="created",
            extra_context={
                "title": _("Most Liked Packages"),
                "heading": _("Most liked 50 packages"),
            },
            template_name="new/package_archive.html",
        ),
        name="liked_packages",
    ),
    path(
        "add/",
        view=AddPackageView.as_view(),
        name="add_package",
    ),
    path(
        "add/validate/",
        view=ValidateRepositoryURLView.as_view(),
        name="validate_repo_url",
    ),
    path(
        "<slug:slug>/edit/",
        view=PackageUpdateView.as_view(),
        name="edit_package",
    ),
    path(
        "<slug:slug>/fetch-data/",
        view=PackageFetchDataView.as_view(),
        name="fetch_package_data",
    ),
    path(
        "<slug:slug>/example/add/",
        view=PackageExampleCreateView.as_view(),
        name="add_example",
    ),
    path(
        "<slug:slug>/example/<int:id>/edit/",
        view=PackageExampleUpdateView.as_view(),
        name="edit_example",
    ),
    path(
        "<slug:slug>/example/<int:id>/delete/",
        view=PackageExampleDeleteView.as_view(),
        name="delete_example",
    ),
    path(
        "<slug:slug>/flag/",
        view=PackageFlagView.as_view(),
        name="flag",
    ),
    path(
        "flag/<int:pk>/approve/",
        view=PackageFlagApproveView.as_view(),
        name="flag_approve",
    ),
    path(
        "flag/<int:pk>/remove/",
        view=PackageFlagRemoveView.as_view(),
        name="flag_remove",
    ),
    path(
        "p/<slug:slug>/opengraph/",
        view=PackageOpenGraphDetailView.as_view(),
        name="package_opengraph",
    ),
    path(
        "p/<slug:slug>/rules/",
        view=PackageRulesView.as_view(),
        name="package_rules",
    ),
    path(
        "p/<slug:slug>/",
        view=PackageDetailView.as_view(),
        name="package",
    ),
    re_path(
        r"^usage/(?P<slug>[-\w]+)/(?P<action>add|remove)/$",
        view=usage,
        name="usage",
    ),
    path(
        "<slug:slug>/documentation/edit/",
        view=PackageDocumentationUpdateView.as_view(),
        name="edit_documentation",
    ),
    path("github-webhook/", view=GitHubWebhookView.as_view(), name="github_webhook"),
    path(
        "<slug:slug>/versions/",
        view=PackageVersionListView.as_view(),
        name="package_versions",
    ),
]
