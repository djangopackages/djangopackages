# Management Commands

These are the management commands that we run to keep the website updated and fresh.

## audit_textfield_max_length

```shell
docker-compose run django python manage.py audit_textfield_max_length
```

## calculate_score

```shell
docker-compose run django python manage.py calculate_score
```

## check_package_examples

```shell
docker-compose run django python manage.py check_package_examples
```

## cleanup_github_projects

```shell
docker-compose run django python manage.py cleanup_github_projects [--limit=<number-of-records>]
```

## fix_grid_element

```shell
docker-compose run django python manage.py fix_grid_element
```

## grid_export

```shell
docker-compose run django python manage.py grid_export
```

## import_classifiers

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
