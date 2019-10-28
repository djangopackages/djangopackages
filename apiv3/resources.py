from django.urls import reverse
from profiles.models import Profile

def base_resource(obj):
    return {
        "absolute_url": obj.get_absolute_url(),
        "created": obj.created,
        "modified": obj.modified,
        "slug": obj.slug,
        "title": obj.title,
    }


def category_resource(cat):
    data = base_resource(cat)
    data.update(
        {
            "description": cat.description,
            "resource_uri": reverse("apiv3:category_detail", kwargs={"slug": cat.slug}),
            "show_pypi": cat.show_pypi,
            "title_plural": cat.title_plural
        }
    )
    return data


def grid_resource(grid):
    data = base_resource(grid)
    data.update(
        {
            "description": grid.description,
            "is_locked": grid.is_locked,
            "resource_uri": reverse("apiv3:grid_detail", kwargs={"slug": grid.slug}),
            "header": grid.header,
            "packages": [
                reverse("apiv3:package_detail", kwargs={'slug':x.slug}) for x in grid.packages.all()
            ]
        }
    )
    return data


def package_resource(package):
    data = base_resource(package)

    try:
        if package.created_by is None or package.created_by.profile is None:
            created_by = None
        else:
            created_by = reverse("apiv3:user_detail", kwargs={"github_account": package.created_by.profile.github_account})
    except Profile.DoesNotExist:
        created_by = None

    try:
        last_modified_by = package.last_modified_by.profile.github_account
    except AttributeError:
        last_modified_by = None

    data.update(
        {
            "category": reverse("apiv3:category_detail", kwargs={"slug": package.category.slug}),
            "commit_list": package.commit_list,
            "commits_over_52": package.commits_over_52(),
            "created_by": created_by,
            "documentation_url": package.documentation_url,
            "grids": [
                reverse("apiv3:grid_detail", kwargs={"slug": x.slug}) for x in package.grids()
            ],
            "last_fetched": package.last_fetched,
            "last_modified_by": last_modified_by,
            "participants": package.participants,
            "pypi_url": package.pypi_url,
            "pypi_version": package.pypi_version(),
            "repo_description": package.repo_description,
            "repo_forks": package.repo_forks,
            "repo_url": package.repo_url,
            "repo_watchers": package.repo_watchers,
            "resource_uri": reverse("apiv3:package_detail", kwargs={"slug": package.slug}),
            "usage_count": package.get_usage_count()
        }
    )
    return data


def user_resource(profile, list_packages=False):
    user = profile.user
    data = {
        "absolute_url": profile.get_absolute_url(),
        "resource_uri": reverse("apiv3:user_detail", kwargs={"github_account": profile.github_account}),
        "created": profile.created,
        "modified": profile.modified,
        "github_account": profile.github_account,
        "username": user.username,
        "date_joined": user.date_joined,
        "last_login": user.last_login,
        "bitbucket_url": profile.bitbucket_url,
        "google_code_url": profile.google_code_url
    }
    if list_packages:
        data['packages'] = [
            reverse("apiv3:package_detail", kwargs={"slug": x.slug}) for x in profile.my_packages()
        ]
    return data
