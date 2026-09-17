# FAQ

## General

### How did Django Packages get started?

- In 2010 We realized there was no effective method for finding apps in the Django community.
- After launch we realized it might be good to use the same software system for other package sets.

### Are there any Case Studies?

- <http://pycon.blip.tv/file/4878766>
- <http://www.slideshare.net/pydanny/django-packages-a-case-study>

### How can I contribute?

Read the page on [contributions].

### How can I add a listing for a new Package or an entirely new Grid?

- Go the Home page, <https://www.djangopackages.org/>
- Click the appropriate button, where a package is a program and a grid is a category.

### Why can't I edit a grid, or why is my new grid not listed?

To cut down on spam, new accounts go through a short review period before they can change grids.

Your account is **trusted** when both of these are true:

- Your Django Packages account is at least **7 days** old.
- The GitHub account you log in with is at least **90 days** old.

Until then:

- **You can still add and edit packages.**
- **You can create new grids, but an admin reviews them before anyone else can see them.** A pending grid is left out of the grid list, search, the homepage, the sitemap, and the API. You can still open it, and it shows a "waiting for review" notice.
- **You can keep editing your own pending grids.** That includes changing the title and description, adding packages, and adding features.
- **You can't edit grids you didn't create.** If you try, you'll see a page explaining the waiting period.

Once your account is trusted, the grids you create are listed right away and you can edit any grid.

#### For site admins

- **Adjusting the waiting periods:** set the `NEW_ACCOUNT_REVIEW_DAYS` (default `7`) and `NEW_GITHUB_ACCOUNT_REVIEW_DAYS` (default `90`) environment variables.
- **Where the GitHub date comes from:** we save the GitHub account's creation date (`created_at`) each time someone logs in. Accounts with no saved date are judged on their Django Packages account age alone.
- **Accounts that skip the review:** staff, superusers, and profiles with **Trusted** checked in the Profile admin.
- **Approving pending grids:** in the Grid admin, filter by **Is Approved**, then use the **Approve selected grids** action.
- **When `RESTRICT_GRID_EDITORS` is on:** grid edits are controlled by Django permissions instead of trust. The one exception is that a new account can still edit its own pending grids.

### What browsers does Django Packages support?

We do formal tests on Chrome, Safari and Firefox.

### How hard is it to add support for a new repo?

We've done a lot of work to make it as straightforward as possible. At PyCon 2011 we launched our formal [Repo Handler API].

### Why does a package not show support for Python 3 on DjangoPackages, but the repository does?

The indicator for support for of Python 3 is support is determined by the data that is fetched from PyPI with the fetch_pypi_dat [method](https://github.com/djangopackages/djangopackages/blob/f259e6f39445cd243ac897af51abb1c06836ef82/package/models.py#L266). Typically if Python 3 is not indicated as being supported it's because there is no PyPI package for the package.

## Reporting Issues with Package Data on Django Packages

### I noticed incorrect or outdated information about a package on Django Packages. How can I report this?

Django Packages primarily fetches data from three sources:

* PyPI
* GitHub
* Bitbucket

If you notice inaccurate information, the best approach is to:

1. **Check the original source**: First, verify if the information is correctly represented in the original source (PyPI, GitHub, or Bitbucket).

2. **For PyPI-related issues**: If the package information on PyPI is incorrect or outdated, the package maintainer should update the metadata in their package configuration (setup.py, pyproject.toml, etc.). Once updated on PyPI, Django Packages will fetch the new metadata during its next update cycle.

3. **For GitHub/Bitbucket repository issues**: If repository information is incorrect, ensure the repository details are properly configured on the source platform.

4. **File an issue on GitHub**: If you've verified the source information is correct but Django Packages is displaying it incorrectly, [open a Bad Data Issue](https://github.com/djangopackages/djangopackages/issues/new/choose)

### How often does Django Packages refresh its data from sources?

Django Packages periodically fetches metadata from PyPI, GitHub, and Bitbucket. This happens through an automated process, but there can sometimes be a delay between when a source is updated and when those changes appear on Django Packages.

## Supported Repo Hosting Services

Django Packages supports GitHub and Bitbucket.

## Troubleshooting

Don't give up!  Submit problems to <http://github.com/djangopackages/djangopackages/issues>. And don't forget:

1. Be polite! We are all volunteers.
2. Spend the time to learn GitHub markup

[contributions]: contributing.md
[repo handler api]: repo_handlers.md
