# Management Commands

These are the management commands that we run to keep the website updated and fresh.

## audit_textfield_max_length

Identifies objects with a text field greater than the maximum length.

```shell
docker-compose run django python manage.py audit_textfield_max_length
```

## calculate_score

Calculates the new star score for all Package objects.

```shell
docker-compose run django python manage.py calculate_score
```

## check_package_examples

Prints out stats about `PackageExample` objects, like the count of active and inactive objects.

For active `PackageExample`s, checks that the URL is valid. If it isn't, the `PackageExample` is marked inactive.

**Optional arguments**:

- `limit`: `int`. Optional. Useful if you want to spot check the `PackageExample` table for bad URLs.

```shell
docker-compose run django python manage.py check_package_examples
```

## cleanup_github_projects

Migrates legacy (http) GitHub packages to https. Migrates existing packages that have moved on GitHub, so their data stays up-to-date.

```shell
docker-compose run django python manage.py cleanup_github_projects [--limit=<number-of-records>]
```

## fix_grid_element

Removes duplicate Element objects.

```shell
docker-compose run django python manage.py fix_grid_element
```

## grid_export

```shell
docker-compose run django python manage.py grid_export
```

## import_classifiers

`classifiers/` app.

The `import_classifiers` management command updates our database against PyPI's trove classifiers.

## import_products

```shell
docker-compose run django python manage.py import_products
```

## import_releases

```shell
docker-compose run django python manage.py import_releases
```

## load_dev_data

Create sample data for local development.

```shell
docker-compose run django python manage.py load_dev_data
```

## package_updater

You can update all the packages with the following command:

```shell
docker-compose run django python manage.py package_updater
```

Warning: This can take a long, long time.

## pypi_find_missing

```shell
docker-compose run django python manage.py pypi_find_missing
```

## pypi_updater

To update packages with the latest data on PyPi, run:

```shell
docker-compose run django python manage.py pypi_updater
```
Warning: This can take a long, long time.

## read_grid_stats

```shell
docker-compose run django python manage.py read_grid_stats
```

## searchv2_build

This command rebuilds and recalculates our search database.

```shell
docker-compose run django python manage.py searchv2_build
```
