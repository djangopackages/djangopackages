# Testing Instructions

In order to run the tests you'll need to make sure that you have the `just` command runner installed.

See the [Install] page for details, or the [Opinionated] install instructions if you want to use the `just` command runner.

## Running the test suite

To run all of the Django Packages tests:

```
docker-compose run django python manage.py test --no-input
```

or with `just`

> just test

To run tests for a particular Django Packages app, for example the feeds app:

```
docker-compose run django python manage.py test feeds
```

or with `just`

> just test feeds

[install]: install.html
[opinionated]: opinionated_install.html
