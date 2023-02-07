# Installation

These instructions install Django Packages on your computer, using Docker.

If you run into problems, see the Troubleshooting section.

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

All of the environment variables and settings that are needed to run the project are stored in  `.env.local.example` file.

```shell
cp .env.local.example .env.local
```

### Build the Docker Containers

Now build the project using docker-compose:

```shell
docker-compose build
```

### Add A GitHub API Token (optional)

Get a [GitHub API token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and set the `GITHUB_TOKEN` variable in `.env.local`
to this value.  This is used by the GitHub repo handler for fetching repo
metadata, and required for certain tests.

### Run the Project

To start the project, run:

```shell
docker-compose up --detach
```

Then point your browser to <http://localhost:8000> and start hacking!

### Create a Local Django Superuser

Now, you'll give yourself an admin account on the locally-running version of Django Packages

Create a Django superuser for yourself, replacing joe with your username/email:

```shell
docker-compose run django python manage.py createsuperuser --username=joe --email=joe@example.com
```

And then login into the admin interface (/admin/) and create a profile for your user filling all the fields with any data.

### pipx

We use `pipx` to install various linters and formatters so you'll need to install it.

Install instructions are available on the here on [pipx].

### Formatters, Linters, and other miscellanea

You'll want to install the various formatters, and linters using the following `pipx` command.

To do this, run the following commands:

```shell
pipx upgrade-all
pipx install djhtml
pipx install tryceratops
pipx install black
pipx install unimport
pipx install pyupgrade-directories
```

## Opinionated Setup

A more [opinionated] set up using the command runner `just` is also available.

[docker]: https://docs.docker.com/install/
[docker-compose]: https://docs.docker.com/compose/install/
[just]: https://github.com/casey/just
[opinionated]: install_opinionated.md
[pipx]: https://pypa.github.io/pipx/
