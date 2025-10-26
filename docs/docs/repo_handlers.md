# Repo Handlers

This document describes the Django Packages Repo Handler API.

Adding a new repo system like GitHub in Django Packages is a relatively straightforward task. You need to provide two things:

1. Add a new repo handler in the apps.models.repos directory that follows the described API
2. Add tests to check your work
3. Document any special settings.
4. Change the SUPPORTED_REPO to include the name of the new repo handler.

If automatic detection is not possible (for example, with self-hosted Forgejo instances),
set the **Repo host** field on a package to the desired handler. The selected handler will
be used even when the repository URL does not match a built-in regex.

## What if my target repo doesn't support all the necessary fields?

Lets say you want to use *GitBlarg*, a new service whose API doesn't provide the number of repo_watchers or participants. In order to handle them you would just set those values until such a time as *GitBlarg* would support the right data.

For example, as you can see in the `apps.models.repos.base_handler.BaseHandler.fetch_metadata()` method, the Package instance that it expects to see is a comma-separated value:

```python
def fetch_metadata(self, package):
    """Accepts a package.models.Package instance:

        return: package.models.Package instance

    Must set the following fields:

        package.repo_watchers (int)
        package.repo_forks (int)
        package.repo_description (text )
        package.participants = (comma-separated value)

    """
    raise NotImplemented()
```

So your code might do the following:

```python
from GitBlargLib import GitBlargAPI


def fetch_metadata(self, package):
    # fetch the GitBlarg data
    git_blarg_data = GitBlargAPI.get(package.repo_name())

    # set the package attributes
    package.repo_watchers = 0  # GitBlagAPI doesn't have this so we set to 0
    package.repo_forks = git_blarg_data.forks
    package.repo_description = git_blarg_data.note
    package.participants = (
        ""  # GitBlagAPI doesn't have this so we set to an empty string
    )

    return package
```

## How about cloning GitBlarg's repos so we can get a better view of the data?

The problem is that developers, designers, and managers will happily put gigabytes of data into a git/hg/svn/fossil/cvs repo. For a single project that doesn't sound like much, but when you are dealing with thousands of packages in a Django Packages instance the scale of the data becomes... well... terrifying. What is now a mild annoyance becomes a staggeringly large problem.

Therefore, pull requests on repo handlers that attempt to solve the problem this way will be summarily **rejected**.
