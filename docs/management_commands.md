# Management Commands

## classifiers app

### import_classifiers

```bash
docker-compose run django python manage.py import_classifiers
```

## core app

### load_dev_data

```bash
docker-compose run django python manage.py load_dev_data
```

## grid app

### fix_grid_element

```bash
docker-compose run django python manage.py fix_grid_element
```

### grid_export

```bash
docker-compose run django python manage.py grid_export
```

### read_grid_stats

```bash
docker-compose run django python manage.py read_grid_stats
```

## package app

### audit_textfield_max_length

### calculate_score

### check_package_examples

### cleanup_github_projects

### package_updater

You can update all the packages with the following command:

```bash
docker-compose run django python manage.py package_updater
```

Warning: This can take a long, long time.

### pypi_find_missing

### pypi_updater

To update packages with the latest data on PyPi, run:

```bash
docker-compose run django python manage.py pypi_updater
```

## products app

### import_products

### import_releases

## searchv2 app

### searchv2_build

To populate the search engine, run:

```bash
docker-compose run django python manage.py searchv2_build
```
