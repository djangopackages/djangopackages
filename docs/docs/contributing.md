# Contributing

First off, we really appreciate that you took the time to read this! That means that you're thinking of making djangopackages.org better in some way. It could certainly use your help.

Here's how to contribute to the development of the code behind djangopackages.org.

## Setup

### Fork on GitHub

Before you do anything else, login/signup on GitHub and fork Django Packages from the [GitHub project].

### Clone Your Fork Locally

If you have git installed, you now clone your git repo using the following command-line argument where `<my-github-name>` is your account name on GitHub:

```shell
git clone git@github.com:<my-github-name>/djangopackages.git
```

## Install Django Packages Locally

These instructions install Django Packages on your computer, using Docker.

If you run into problems, see the Troubleshooting section. If that doesn't solve your issue please report them via our [issue tracker].

### Set up Tooling

You'll want to make sure your local environment is ready by installing the following tools.

#### Docker

If you don't have them installed yet, install [Docker] and [Compose].

### Set Up Options

There are two options for setting up your development environment:

1. Standard - use standard docker compose commands in your terminal
2. [Just] - use the `just` command runner in your terminal

### Set Up Your Development Environment

All of the environment variables and settings that are needed to run the project are stored in  `.env.local.example` file.

In order to run the project, you'll need to run the following command:

=== "Standard"

    ```shell
    cp .env.local.example .env.local
    ```

=== "Just"

    ```shell
    just setup
    ```

#### Build the Docker Containers

Now build the project using Docker Compose:

=== "Standard"

    ```shell
    docker compose build
    ```

=== "Just"

    ```shell
    just build
    ```


#### Add A GitHub API Token (optional)

Get a [GitHub API token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and set the `GITHUB_TOKEN` variable in `.env.local`
to this value.  This is used by the GitHub repo handler for fetching repo
metadata, and required for certain tests.

#### Run the Project

To start the project, run:

=== "Standard"

    ```shell
    docker compose up --detach
    ```

=== "Just"

    ```shell
    just up --detach
    ```


Then point your browser to <http://localhost:8000> and start hacking!

#### Create a Local Django Superuser

Now, you'll give yourself an admin account on the locally-running version of Django Packages

Create a Django superuser for yourself, replacing joe with your username/email:

=== "Standard"

    ```shell
    docker compose run django python -m manage createsuperuser --username=joe --email=joe@example.com
    ```

=== "Just"

    ```shell
    just createsuperuser joe joe@example.com
    ```

And then login into the admin interface (/admin/) and create a profile for your user filling all the fields with any data.

#### Load Sample Data

We use a **Mock** system of creating sample data in our tests and for running a development version of the site. To create some development data, just run:

=== "Standard"

    ```shell
    docker compose run --rm django python -m manage load_dev_data
    ```

=== "Just"

    ```shell
    just management-command load_dev_data
    ```


#### Rebuild Search Indexes

Next, we need to rebuild and recalculate our search database.

=== "Standard"

    ```shell
    docker compose run --rm django python -m manage searchv2_build
    ```

=== "Just"

    ```shell
    just management-command searchv2_build
    ```

While the search v2 is our current default search algorithm, we have an experimental v3 that we are testing. To rebuild and recalculate our search database using the v3 engine, we run:

=== "Standard"

    ```shell
    docker compose run --rm django python -m manage searchv3_build
    ```

=== "Just"

    ```shell
    just management-command searchv3_build
    ```

#### Formatters, Linters, and other miscellanea

[Pre-commit] is a tool which helps to organize our linters and auto-formatters. Pre-commit runs before our code gets committed automatically or we may run it by hand. Pre-commit runs automatically for every pull request on GitHub too.

To install the pre-commit hooks:

```shell
pip install pre-commit
pre-commit install
```

To run all pre-commit rules by hand:

```shell
pre-commit run --all-files
```

To run a pre-commit rule by hand:

```shell
pre-commit run ruff
```

[compose]: https://docs.docker.com/compose/install/
[docker]: https://docs.docker.com/install/
[just]: https://github.com/casey/just
[pre-commit]: https://github.com/pre-commit/pre-commit

## Issues!

The list of outstanding Django Packages feature requests and bugs can be found on our GitHub [issue tracker]. Pick an unassigned issue that you think you can accomplish, add a comment that you are attempting to do it, and shortly your own personal label matching your GitHub ID will be assigned to that issue.

Feel free to propose issues that aren't described!

### Tips

1. **starter** labeled issues are deemed to be good low-hanging fruit for newcomers to the project, Django, or even Python.
2. **doc** labeled issues must only touch content in the docs folder.

## Setting up topic branches and generating pull requests

While it's handy to provide useful code snippets in an issue, it is better for
you as a developer to submit pull requests. By submitting pull request your
contribution to Django Packages will be recorded by GitHub.

In git it is best to isolate each topic or feature into a "topic branch". While
individual commits allow you control over how small individual changes are made
to the code, branches are a great way to group a set of commits all related to
one feature together, or to isolate different efforts when you might be working
on multiple topics at the same time.

While it takes some experience to get the right feel about how to break up
commits, a topic branch should be limited in scope to a single `issue` as
submitted to an issue tracker.

Also since GitHub pegs and syncs a pull request to a specific branch, it is the
**ONLY** way that you can submit more than one fix at a time. If you submit
a pull from your develop branch, you can't make any more commits to your develop
without those getting added to the pull.

To create a topic branch, its easiest to use the convenient `-b` argument to `git
checkout`:

```shell
git checkout -b fix-broken-thing
```

```shell
Switched to a new branch 'fix-broken-thing'
```

You should use a verbose enough name for your branch so it is clear what it is
about. Now you can commit your changes and regularly merge in the upstream
develop as described below.

When you are ready to generate a pull request, either for preliminary review,
or for consideration of merging into the project you must first push your local
topic branch back up to GitHub:

```shell
git push origin fix-broken-thing
```

Now when you go to your fork on GitHub, you will see this branch listed under
the "Source" tab where it says "Switch Branches". Go ahead and select your
topic branch from this list, and then click the "Pull request" button.

Here you can add a comment about your branch. If this in response to
a submitted issue, it is good to put a link to that issue in this initial
comment. The repo managers will be notified of your pull request and it will
be reviewed (see below for best practices). Note that you can continue to add
commits to your topic branch (and push them up to GitHub) either if you see
something that needs changing, or in response to a reviewer's comments. If
a reviewer asks for changes, you do not need to close the pull and reissue it
after making changes. Just make the changes locally, push them to GitHub, then
add a comment to the discussion section of the pull request.

## Pull upstream changes into your fork regularly

Django Packages is advancing quickly. It is therefore critical that you pull upstream changes from main into your fork on a regular basis. Nothing is worse than putting in a days of hard work into a pull request only to have it rejected because it has diverged too far from main branch.

To pull in upstream changes:

```shell
git remote add upstream https://github.com/djangopackages/djangopackages.git
git fetch upstream main
```

Check the log to be sure that you actually want the changes, before merging:

```shell
git log upstream/main
```

Then merge the changes that you fetched:

```shell
git merge upstream/main
```

For more info, see <http://help.github.com/fork-a-repo/>

## How to get your pull request accepted

We want your submission. But we also want to provide a stable experience for our users and the community. Follow these rules and you should succeed without a problem!

### Run the tests!

Before you submit a pull request, please run the entire Django Packages test suite via:

```shell
docker compose run django pytest
```

The first thing the core committers will do is run this command. Any pull request that fails this test suite will be **rejected**.

### If you add code/views you need to add tests!

We've learned the hard way that code without tests is undependable. If your pull request reduces our test coverage because it lacks tests then it will be **rejected**.

For now, we use the Django Test framework (based on unittest).

Also, keep your tests as simple as possible. Complex tests end up requiring their own tests. We would rather see duplicated assertions across test methods then cunning utility methods that magically determine which assertions are needed at a particular stage. Remember: `Explicit is better than implicit`.

### Don't mix code changes with whitespace cleanup

If you change two lines of code and correct 200 lines of whitespace issues in a file the diff on that pull request is functionally unreadable and will be **rejected**. Whitespace cleanups need to be in their own pull request.

### Keep your pull requests limited to a single issue

Django Packages pull requests should be as small/atomic as possible. Large, wide-sweeping changes in a pull request will be **rejected**, with comments to isolate the specific code in your pull request. Some examples:

1. If you are making spelling corrections in the docs, don't modify the settings.py file ([pydanny] is guilty of this mistake).
2. Adding new [Repo Handlers](repo_handlers.md) must not touch the Package model or its methods.
3. If you are adding a new view don't '_cleanup_' unrelated views. That cleanup belongs in another pull request.
4. Changing permissions on a file should be in its own pull request with explicit reasons why.

### Follow PEP-8 and keep your code simple!

Memorize the Zen of Python:

```shell
>>> python -c 'import this'
```

Please keep your code as clean and straightforward as possible. When we see more than one or two functions/methods starting with `_my_special_function` or things like `__builtins__.object = str` we start to get worried. Rather than try and figure out your brilliant work we'll just **reject** it and send along a request for simplification.

Furthermore, the pixel shortage is over. We want to see:

- `package` instead of `pkg`
- `grid` instead of `g`
- `my_function_that_does_things` instead of `mftdt`

### Test any css/layout changes in multiple browsers

Any css/layout changes need to be tested in Chrome, Safari, Firefox, IE8, and IE9 across Mac, Linux, and Windows. If it fails on any of those browsers your pull request will be **rejected** with a note explaining which browsers are not working.

## How pull requests are checked, tested, and done

First we pull the code into a local branch:

```shell
git checkout -b <branch-name> <submitter-github-name>
git pull git://github.com/<submitter-github-name/djangopackages.git main
```

Then we run the tests:

```shell
python -m manage test --settings=settings.test
```

We finish with a merge and push to GitHub:

```shell
git checkout main
git merge <branch-name>
git push origin main
```

[github project]: https://github.com/djangopackages/djangopackages
[issue tracker]: https://github.com/djangopackages/djangopackages/issues
[pydanny]: http://pydanny.com
