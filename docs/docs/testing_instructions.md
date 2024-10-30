# Testing Instructions

In order to run the tests you'll need to make sure that you have the [just] command runner installed.

See the [Install] page for details.

## Running the full test suite

To run all of the Django Packages tests:

```shell
docker compose run django pytest
```

Alternatively, you can use [just]:

```shell
just test
```

## Selectively running tests

To run tests for a particular Django Packages app, for example the feeds app:

```shell
docker compose run django pytest feeds
```

Alternatively, you can use [just]:

```shell
just test feeds
```

[just]: https://github.com/casey/just
[Install]: contributing.md#install-django-packages-locally
