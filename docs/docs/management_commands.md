# Management Commands

These are the management commands that we run to keep the website updated and fresh.

## audit_textfield_max_length

Identifies objects with a text field greater than the maximum length.

```shell
docker compose run django uv run manage.py audit_textfield_max_length
```

## calculate_score

Calculates the new star score for all Package objects.

```shell
docker compose run django uv run manage.py calculate_score
```

## check_package_examples

Prints out stats about `PackageExample` objects, like the count of active and inactive objects.

For active `PackageExample`s, checks that the URL is valid. If it isn't, the `PackageExample` is marked inactive.

**Optional arguments**:

- `limit`: `int`. Optional. Useful if you want to spot check the `PackageExample` table for bad URLs.

```shell
docker compose run django uv run manage.py check_package_examples
```

## cleanup_github_projects

Migrates legacy (http) GitHub packages to https. Migrates existing packages that have moved on GitHub, so their data stays up-to-date.

```shell
docker compose run django uv run manage.py cleanup_github_projects [--limit=<number-of-records>]
```

## evaluate_grid_elements

Reads each grid cell back as one of five support levels: `supported`, `partial`, `not_supported`, `unknown`, or `not_applicable`. The cells are free text with no convention beyond a loose icon legend, so the same answer turns up as "yes", "+", "Yes, since 2.0", and a sentence.

Cells that are already a legend token ("yes", "no", "+", "-") are mapped locally and cost nothing.

Read-only. Requires `TYPESAFE_API_KEY`, and each cell sent to the model costs one API call.

**Optional arguments**:

- `--limit`: `int`. Cells to read. `0` means all. Default `20`.
- `--slug`: `str`. Only read one grid.
- `--feature`: `str`. Only features whose title matches this text.
- `--all-cells`: flag. Send the legend cells to the model too, instead of mapping them locally.
- `--only-problems`: flag. Print only the placeholders and unknowns.
- `--min-confidence`: `float`. Bar for counting a verdict. Default `0.85`.

```shell
docker compose run django uv run manage.py evaluate_grid_elements --slug email
```

## evaluate_grid_packages

Asks whether each package belongs in the grid it is listed on, and which installation type it looks like. Use `--category other` to sweep the "Other" backlog; a sweep reviews each package once rather than once per grid it appears on, and drops the grid columns, which are not meaningful once the rows are deduplicated.

The report ends with the moves grouped by destination.

Read-only unless an `--apply` flag is passed. Requires `TYPESAFE_API_KEY`, and each row costs one API call.

**Optional arguments**:

- `--limit`: `int`. Packages to review. `0` means all. Default `10`.
- `--slug`: `str`. Only review one grid.
- `--category`: `str`. Only packages filed under this installation type, e.g. `other`.
- `--only-problems`: flag. Print only the flagged rows.
- `--min-confidence`: `float`. Bar for acting on a verdict. Default `0.85`.
- `--apply-moves`: flag. **Writes.** Offer to refile each miscategorised package, one at a time.
- `--apply-removals`: flag. **Writes.** Offer to drop each off-topic package from its grid. Deletes the grid row, never the package. Cannot be combined with `--category`.
- `--yes`: flag. Answer yes to every prompt. Only means anything alongside an `--apply` flag.

Each prompt shows the package's own description and repo URL, and takes `y`, `n`, or `q` to stop and leave the rest untouched.

```shell
docker compose run django uv run manage.py evaluate_grid_packages --category other --limit 50
docker compose run django uv run manage.py evaluate_grid_packages --category other --apply-moves
```

## evaluate_grids

Scores each comparison grid on three rubrics (`UNUSABLE`, `WEAK`, `DECENT`, `STRONG`): whether the packages share one focused topic, whether the title and description are specific, and whether there is enough there to work as a comparison. Also asks whether a field of competing packages exists for the topic at all.

A grid with fewer than two packages is listed for removal on the count alone, without asking the model.

Read-only unless an `--apply` flag is passed. Requires `TYPESAFE_API_KEY`, and each grid costs one API call.

**Optional arguments**:

- `--limit`: `int`. Grids to review. `0` means all. Default `5`.
- `--slug`: `str`. Review a single grid.
- `--min-packages`: `int`. Skip grids with fewer packages than this.
- `--min-confidence`: `float`. Bar for counting a verdict. Default `0.85`.
- `--apply-unapprove`: flag. **Writes.** Offer to hide each grid listed for removal by clearing `is_approved`. The grid, its features, and its cells all survive, so this is reversible from the admin.
- `--apply-delete`: flag. **Writes, irreversibly.** Offer to delete each grid listed for removal, taking its features and cells with it. Does not accept `--yes`.
- `--yes`: flag. Answer yes to every prompt. Refused with `--apply-delete`.

The two `--apply` flags are mutually exclusive. Each prompt shows the grid's title, description, and how many packages, features, and cells it holds.

```shell
docker compose run django uv run manage.py evaluate_grids --limit 0 --min-packages 0
docker compose run django uv run manage.py evaluate_grids --limit 0 --apply-unapprove
```

## evaluate_packages

Reviews the packages that are on no comparison grid, which `evaluate_grid_packages` cannot reach because it walks grid rows. Asks which installation type the package looks like, and whether its description says enough to tell.

Packages whose description is the problem are reported separately and never offered for refiling, since there is nothing to judge the move on.

Read-only unless `--apply-moves` is passed. Requires `TYPESAFE_API_KEY`, and each package costs one API call.

**Optional arguments**:

- `--limit`: `int`. Packages to review. `0` means all. Default `10`.
- `--category`: `str`. Only packages filed under this installation type, e.g. `other`.
- `--only-problems`: flag. Print only the moves and the packages missing a description.
- `--min-confidence`: `float`. Bar for acting on a verdict. Default `0.85`.
- `--apply-moves`: flag. **Writes.** Offer to refile each miscategorised package, one at a time.
- `--yes`: flag. Answer yes to every prompt. Only means anything alongside `--apply-moves`.

```shell
docker compose run django uv run manage.py evaluate_packages --category other --limit 50
```

## fix_grid_element

Removes duplicate Element objects.

```shell
docker compose run django uv run manage.py fix_grid_element
```

## grid_export

```shell
docker compose run django uv run manage.py grid_export
```

## import_classifiers

The `import_classifiers` management command updates our database against PyPI's trove classifiers.

## import_products

Imports all packages from endoflife.date, and sets some packages to active.

```shell
docker compose run django uv run manage.py import_products
```

## import_releases

Imports Release data for Packages from endoflife.date.

```shell
docker compose run django uv run manage.py import_releases
```

## load_dev_data

Create sample data for local development.

```shell
docker compose run django uv run manage.py load_dev_data
```

## package_updater

Updates all the GitHub Packages in the database.

Warning: This can take a long, long time.

**Optional Arguments**:

- `limit`: `int`. Pass this value if you want to update a specific number of packages.

```shell
docker compose run django uv run manage.py package_updater
```

## pypi_find_missing

Shows count of Packages without pypi URLs or with outdated pypi URLs

```shell
docker compose run django uv run manage.py pypi_find_missing
```

## pypi_updater

Updates all the packages in the system by checking against their PyPI data.

```shell
docker compose run django uv run manage.py pypi_updater
```
Warning: This can take a long, long time.

## read_grid_stats

```shell
docker compose run django uv run manage.py read_grid_stats
```

## build_search_v3

Builds the SearchV3 index for package and grid search results.

```shell
docker compose run django uv run manage.py build_search_v3
```
