# Opinionated Installation

These instructions install Django Packages on your computer, using Docker.

## Set up Tooling

You'll want to make sure your local environment is ready by installing the following tools.

### Docker

If you don't have them installed yet, install [Docker] and [docker-compose].

### Grab a Local Copy of the Project

[Fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) the Django Packages project

Clone the Django Packages project using git:

```shell
git clone git@github.com:<your-github-username>/djangopackages.git
cd djangopackages
```

### Set Up Your Development Environment

In order to run the project, you'll need to run the following command:

```shell
just setup
```

### Add A GitHub API Token

Get a [GitHub API token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and set the `GITHUB_TOKEN` variable in `.env.local`
to this value.  This is used by the GitHub repo handler for fetching repo
metadata, and required for certain tests.

### Build the Docker Containers

Now build the project using docker-compose:

```shell
just build
```

### Run the Project

To start the project, run:

```shell
just up --detach
```

Then point your browser to <http://localhost:8000> and start hacking!

### Create a Local Django Superuser

Now, you'll give yourself an admin account on the locally-running version of Django Packages

Create a Django superuser for yourself, replacing joe with your username/email:

```shell
just createsuperuser joe joe@example.com
```

And then login into the admin interface (/admin/) and create a profile for your user filling all the fields with any data.

### Load Sample Data

We use a **Mock** system of creating sample data in our tests and for running a development version of the site. To create some development data, just run:

```shell
just management-command load_dev_data
```

### just

We use the command runner [just]. Install instructions are available on the [just] GitHub page.


### Formatters, Linters, and other miscellanea

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

[docker-compose]: https://docs.docker.com/compose/install/
[docker]: https://docs.docker.com/install/
[just]: https://github.com/casey/just
[opinionated]: install_opinionated.md
[pre-commit]: https://github.com/pre-commit/pre-commit
