# Django Packages

Django Packages helps you easily identify and compare good apps, frameworks, plugins, and other types of packages, using comparison grids.

## Badges

[![image](https://github.com/djangopackages/djangopackages/actions/workflows/actions.yml/badge.svg)](https://github.com/djangopackages/djangopackages/actions/workflows/actions.yml) [![Documentation Status](https://readthedocs.org/projects/djangopackages/badge/?version=latest)](https://docs.djangopackages.org/en/latest/?badge=latest) [![Updates](https://pyup.io/repos/github/djangopackages/djangopackages/shield.svg)](https://pyup.io/repos/github/djangopackages/djangopackages/) [![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/djangopackages/)

## Features

-   Comparison grids with wiki-like editing capability
    -   Add packages to grid
    -   Add/edit grid features
-   Storage of package info, fetched from public APIs
    -   PyPI
    -   GitHub
    -   Bitbucket
    -   GitLab (coming soon)
-   Basic search
    -   Autocomplete packages/grids
-   Social features:
    -   "I use this" button
    -   Latest packages featured on homepage
-   "Add package" and "Add grid" forms

## Quickstart

For detailed installation instructions, consult the [docs](https://docs.djangopackages.org/en/latest/contributing/#install-django-packages-locally).

To download, install and start the local server for development, simply run:

```shell
git clone git@github.com:djangopackages/djangopackages.git
cd djangopackages
cp .env.local.example .env.local
docker compose build
docker compose up
```

Then point your browser to http://localhost:8000 and start hacking!

If you are running into conflicting port issues, we have an override file which re-maps Django (port: 18000) and Postgres (port: 45432). To activate it, simply run:

```shell
docker compose build
docker compose up
````

To run tests, run:

```shell
docker compose run django pytest
```

## The Site

https://djangopackages.org

## The Documentation

The documentation is hosted at https://docs.djangopackages.org/en/latest

## License

The code is open-source and licensed under the MIT license.

# Credits

For Django Dash 2010, [@pydanny](https://github.com/pydanny/) and [@audreyr](https://github.com/audreyr/) created [Django Packages](https://www.djangopackages.org/).

They are joined by a host of core developers and contributors. See [contributors](CONTRIBUTORS.md).
