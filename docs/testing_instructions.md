# Testing Instructions

In order to run the tests you'll need to make sure that you have the `just` command runner installed.

See the [Install] page for details, or the [Opinionated Install] instructions if you want to use the `just` command runner.

## Running the full test suite

To run all of the Django Packages tests:

```shell
docker-compose run django python manage.py test --no-input
```

or with pytest:

```shell
docker-compose run pytest
```

or with `just`:

```shell
just test
```

## Selectively running tests

To run tests for a particular Django Packages app, for example the feeds app:

```shell
docker-compose run django python manage.py test feeds
```

or with pytest:

```shell
docker-compose run pytest feeds
```

or with `just`:

```shell
just test feeds
```

[Install]: install.md
[Opinionated Install]: install_opinionated.md
