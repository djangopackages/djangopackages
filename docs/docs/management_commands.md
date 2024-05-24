# Management Commands

These are the management commands that we run to keep the website updated and fresh.

## audit_textfield_max_length

Identifies objects with a text field greater than the maximum length.

```shell
docker compose run django python -m manage audit_textfield_max_length
```

## calculate_score

Calculates the new star score for all Package objects.

```shell
docker compose run django python -m manage calculate_score
```

## check_package_examples

Prints out stats about `PackageExample` objects, like the count of active and inactive objects.

For active `PackageExample`s, checks that the URL is valid. If it isn't, the `PackageExample` is marked inactive.

**Optional arguments**:

- `limit`: `int`. Optional. Useful if you want to spot check the `PackageExample` table for bad URLs.

```shell
docker compose run django python -m manage check_package_examples
```

## cleanup_github_projects

Migrates legacy (http) GitHub packages to https. Migrates existing packages that have moved on GitHub, so their data stays up-to-date.

```shell
docker compose run django python -m manage cleanup_github_projects [--limit=<number-of-records>]
```

## fix_grid_element

Removes duplicate Element objects.

```shell
docker compose run django python -m manage fix_grid_element
```

## grid_export

```shell
docker compose run django python -m manage grid_export
```

## import_classifiers

The `import_classifiers` management command updates our database against PyPI's trove classifiers.

## import_products

Imports all packages from endoflife.date, and sets some packages to active.

```shell
docker compose run django python -m manage import_products
```

## import_releases

Imports Release data for Packages from endoflife.date.

```shell
docker compose run django python -m manage import_releases
```

## load_dev_data

Create sample data for local development.

```shell
docker compose run django python -m manage load_dev_data
```

## package_updater

Updates all the GitHub Packages in the database.

Warning: This can take a long, long time.

**Optional Arguments**:

- `limit`: `int`. Pass this value if you want to update a specific number of packages.

```shell
docker compose run django python -m manage package_updater
```

## pypi_find_missing

Shows count of Packages without pypi URLs or with outdated pypi URLs

```shell
docker compose run django python -m manage pypi_find_missing
```

## pypi_updater

Updates all the packages in the system by checking against their PyPI data.

```shell
docker compose run django python -m manage pypi_updater
```
Warning: This can take a long, long time.

## read_grid_stats

```shell
docker compose run django python -m manage read_grid_stats
```

## searchv2_build

This command rebuilds and recalculates our search database.

```shell
docker compose run django python -m manage searchv2_build
```
