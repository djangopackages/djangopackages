# Management Commands

These are the management commands that we run to keep the website updated and fresh.

## audit_textfield_max_length

Identifies objects with a text field greater than the maximum length.

```shell
docker compose run django uv run manage.py audit_textfield_max_length
```

## calculate_score

Recalculates `Package.score` (0 to 100, see `package/scoring.py`) for all Package objects. Only packages whose score changed are written.

```shell
docker compose run django uv run manage.py calculate_score
```

## compare_scores

Dry run of the package score as `searchv3/rules.py` computes it against the stored `Package.score`. Prints both distributions and, for every approved grid, what the comparison table would show under each, at the current `PACKAGE_SCORE_MIN` or the `--new-min` given. Writes nothing. Use it to preview a rule change or a new cutoff, and to check that stored scores are current. The points-by-rule table also shows the mean activity factor and how many packages it leaves at 0.

```shell
docker compose run django uv run manage.py compare_scores [--new-min 30] [--grid <slug>] [--csv scores.csv]
```

## cleanup_github_projects

Migrates legacy (http) GitHub packages to https. Migrates existing packages that have moved on GitHub, so their data stays up-to-date.

```shell
docker compose run django uv run manage.py cleanup_github_projects [--limit=<number-of-records>]
```

## evaluate_grid_elements

Archived and deprecated packages are skipped by every one of these commands. Reviewing a dead package buys nothing, and in production 939 of the 5,836 packages are archived or deprecated, including 83 of the 680 still sitting in "Other". Pass `--include-archived` to put them back.

Reads each grid cell back as one of five support levels: `supported`, `partial`, `not_supported`, `unknown`, or `not_applicable`. The cells are free text with no convention beyond a loose icon legend, so the same answer turns up as "yes", "+", "Yes, since 2.0", and a sentence.

Cells that are already a legend token ("yes", "no", "+", "-") are mapped locally and cost nothing.

Read-only. Requires `TYPESAFE_API_KEY`, and each cell sent to the model costs one API call.

**Optional arguments**:

- `--limit`: `int`. Cells to read. `0` means all. Default `20`.
- `--slug`: `str`. Only read one grid.
- `--feature`: `str`. Only features whose title matches this text.
- `--all-cells`: flag. Send the legend cells to the model too, instead of mapping them locally.
- `--include-archived`: flag. Read cells for archived and deprecated packages too. Skipped by default.
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
- `--include-archived`: flag. Review archived and deprecated packages too. Skipped by default.
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
- `--include-archived`: flag. Review archived and deprecated packages too. Skipped by default.
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

## pypi_stats

Fetches each package's downloads over the last month from
[pypistats.org](https://pypistats.org) into `Package.pypi_downloads`, which the
package list can sort by. One request per package, two seconds apart, so a full
pass over the catalogue takes about three hours.

```shell
just run pypi_stats                      # every package with a PyPI URL
just run pypi_stats --slug django-nh3    # one package
just run pypi_stats --delay 1            # faster, at the API's mercy
```

The scheduled form is the `pypi-stats` job in `init_scheduled_jobs`, weekly on
Sunday morning.

## recategorize_from_grids

Refiles packages into the category the grids they are already on imply.

A grid is a topic somebody curated by hand, so a package sitting on `Cookiecutters` has already been told what it is and the category field just never caught up. This reads that off the grid rather than asking Jev, so unlike `evaluate_packages` it costs nothing and needs no API key.

The grid-to-category map lives in the command. Only grids where packages filed under `other` were the majority or near-majority of the members are in it, since those are the ones where the category is clearly what's wrong.

A package whose grids point at two different categories is reported and never moved. That is a judgement call, not a backfill.

Read-only unless `--apply` is passed.

**Optional arguments**:

- `--from`: `str`. Comma-separated categories to move packages out of. Default `other`.
- `--to`: `str`. Only propose moves into this category. Default is all of them.
- `--limit`: `int`. Stop after this many. `0` means all. Default `0`.
- `--apply`: flag. **Writes.** Offer each move, one at a time.
- `--yes`: flag. Answer yes to every prompt. Only means anything alongside `--apply`.

```shell
docker compose run django uv run manage.py recategorize_from_grids
docker compose run django uv run manage.py recategorize_from_grids --to developer-tools --apply
```

Review the `developer-tools` half rather than running it with `--yes`. The `Linters`, `Template Linters` and `Testing tools` grids are tight, but `Developer Tools` is a broad grid and a few of its members are ordinary apps. The `starter-projects` and `deployment` halves are safe to run straight through.

## read_grid_stats

```shell
docker compose run django uv run manage.py read_grid_stats
```

## build_search_v3

Builds the SearchV3 index for package and grid search results.

```shell
docker compose run django uv run manage.py build_search_v3
```
## build_probe_profiles

Fills in each package's probe profile from the PyPI metadata we already
store, so it reads nothing from the network and clones nothing.

It writes one row per package into `PackageProbe`. `python_versions` and
`django_versions` are JSON lists, oldest first, and `python_source` and
`django_source` record where each came from: Trove classifiers where they
exist, otherwise `requires_python` or the Django pin in `requires_dist`,
resolved against the real release cycles in `products.Release`.
`dependencies` is a JSON list of `{name, specifier, extra, marker}`.

A specifier with no upper bound is only read as far as the day the package
was last published. `Django>=1.8` in a release from 2021 resolves to 1.8
through 3.2, not through 6.1: the lower bound is a minimum, and nothing
about it says the package was ever run on a Django that shipped afterwards.
A pin that does bound itself above is taken at face value whatever the date,
and classifiers are never capped, since they name exact versions. A package
we cannot date resolves to nothing from its specifiers, because there is no
point in time to read them against.

Grouping across packages is still a single query, because Postgres can
unnest the list:

```sql
SELECT dep->>'name', count(DISTINCT p.package_id)
FROM probes_packageprobe p, jsonb_array_elements(p.dependencies) AS dep
WHERE dep->>'extra' = ''
GROUP BY 1 ORDER BY 2 DESC;
```

Dependencies behind an extra are stored and marked rather than dropped, since
what anyone depends on and what a default install pulls in are different
questions. They do not count as evidence of Django support: Celery declares
`Django>=2.2.28; extra == "django"` and is not a Django package.

In production 64% of eligible packages carry Python classifiers, 37% carry
Django ones, and 71% have at least one usable signal. About half have no
`requires_dist` at all, because that metadata postdates them. That gap is
what the AST scan is for.

```shell
docker compose run django uv run manage.py build_probe_profiles [--slug=<slug>] [--limit=<number>] [--min-score=<n>] [--dry-run]
```

## check_package_sources

Decides which packages are worth keeping a source checkout of, by setting
`Package.probe`. It asks two questions, neither of which needs a clone: does
the git remote still answer (`git ls-remote`), and is the project still on
PyPI.

`probe` is a tri-state. Null means nobody has looked yet, so a new package is
picked up by the next run and is treated as worth trying in the meantime.
False excludes it from `sync_package_repos` and `scan_package_repos`, with
`probe_note` recording why and `probe_checked_at` when.

Already-decided packages are left alone, so a routine run only covers new
ones. Pass `--recheck` to revisit, since a repo that was private last month
may be public today.

```shell
docker compose run django uv run manage.py check_package_sources [--slug=<slug>] [--limit=<number>] [--recheck] [--timeout=<seconds>] [--dry-run]
```

## sync_package_repos

The checkouts are not mounted by default. Copy `compose.override.yml.example`
to `compose.override.yml` to mount them, which puts them in a sibling of the
checkout rather than inside it, so no tool that walks the project tree has to
learn to skip thousands of other people's repositories.

Clones or updates local git checkouts of the packages we index, so their
source can be scanned. It covers packages with both a repo we can clone from
(GitHub, GitLab, Bitbucket or Codeberg) and a PyPI release, which in
production is 4,714 of 5,849. A named `--slug` is fetched whether or not it
meets that bar.

So is a package tagged `awesome-list` in `Package.tags`: awesome-django,
awesome-django-rest-framework and awesome-wagtail have no PyPI release and
nothing to import, but their READMEs are the data we read back when checking
which listed packages have gone quiet. Add the tag in the admin to track
another list.

## tag_awesome_packages

Reads the README out of each `awesome-list` package's checkout and gives
every repository or PyPI project it links to the list's slug as a tag, so
`Package.objects.filter(tags__contains=["awesome-django"])` is the set of
packages Awesome Django lists today. A package that drops off the list loses
the tag on the next run; a list whose checkout has no README changes nothing.

```shell
just run tag_awesome_packages              # every list
just run tag_awesome_packages --sync       # pull the checkouts first
just run tag_awesome_packages --slug awesome-wagtail --dry-run
```

The scheduled form is the `awesome-lists` job in `init_scheduled_jobs`, which
runs `probes.tasks.refresh_awesome_lists` nightly: sync each list, then tag.

`--min-score` defaults to 0, which halves that again to around 1,960. A
negative score is not a popularity judgement: the staleness penalty only
overtakes the stars after roughly thirty months without a commit, so below
zero reads as abandoned whether a package has three stars or three thousand.
Zero itself is kept, since a package added yesterday has no stars and scores
zero.

Pass `--min-score=-500` to reach the abandoned ones. That is the set worth
scanning when the question is which packages are broken against modern
Django, because that is exactly where removed APIs survive. Checkouts live under `PACKAGE_REPO_ROOT` (`/repos` in
the container), one directory per
package slug, and are refreshed in place rather than re-cloned.

Clones are shallow by default, since only the working tree is read. Packages
whose `repo_url` is not on a host we can clone from are skipped and counted.
Git is run with prompting disabled, so a private or deleted repo fails
immediately instead of blocking on a credential prompt.

```shell
docker compose run django uv run manage.py sync_package_repos [--slug=<slug>] [--limit=<number>] [--depth=<n>] [--missing-only] [--dry-run]
```

## Running the probe pipeline on a schedule

The commands above are the right tool for building the pipeline and for
one-off runs. For keeping the catalogue current they run as Django Q jobs,
registered with `init_scheduled_jobs`:

| job | when | what |
| --- | --- | --- |
| `probe-refresh` | 02:17 | `probes.tasks.queue_probe_refresh` queues one task per package |
| `probe-profiles` | 05:12 | `build_probe_profiles` |
| `probe-catalog` | 06:12 | `build_probe_catalog` |

The fan-out queues two kinds of task. `check_package_source` revisits
packages nobody has decided on yet and packages whose verdict is more than
30 days old, so a repo that goes private or comes back is noticed within a
month. `refresh_package_checkout` syncs one checkout, records what it is
imported as, and scans it, for every package `sync_package_repos` would
cover. A checkout still on the commit its profile was read from is not
scanned again. Each task is independent, so the cluster works through them
in parallel and one dead repo costs one failed task rather than a stalled
run.

The worker needs the checkouts volume mounted at `PACKAGE_REPO_ROOT`, the
same as the web container, since that is where the tasks read and write.

```shell
docker compose run django uv run manage.py init_scheduled_jobs --only probe-refresh --only probe-profiles --only probe-catalog
docker compose run django uv run manage.py init_scheduled_jobs --list
```

Without `--only` the command adds every job it knows about, including the
search rebuild and the two package updaters, so pass it on an install where
those are run some other way.

## The probes app

All of this lives in the `probes` app: the checkouts, the AST scan, the
profiles and the catalogue. It uses `django-probe`'s AST visitor and probe
registry, whose importable name is `django_probe`, so the two sit side by
side without colliding. The flags that decide whether a package gets probed
at all stay on `package.Package`, because they describe the package.

Three tables:

- `probes.PackageProbe`, one row per package: the versions it claims, the
  symbols and patterns its source uses, and when we last looked.
- `probes.ProbeSymbol`, one row per thing a scan can name. This is where a
  deprecation or a removal version belongs, since that is a fact about the
  API rather than about any package calling it.
- `probes.Library`, the distribution name next to the import name, with the
  toggle that decides which libraries a scan counts.

### The order they run in

Six commands, and the order matters because each one reads what the one
before it wrote.

1. `check_package_sources` decides which packages are worth a checkout at
   all and sets `Package.probe`. Everything downstream filters on that flag,
   so this goes first. Network bound: one `git ls-remote` and one PyPI
   lookup per package.
2. `sync_package_repos` clones or pulls the checkouts for the packages that
   survived step 1. The slowest step, and the only one that needs disk.
3. `build_probe_libraries` reads the top level packages out of those
   checkouts to learn what each distribution is imported as. Needs the
   checkouts, and the scan needs its answers, so it sits between them.
4. `scan_package_repos` walks the checkouts with the AST probe and writes
   the symbols, patterns and settings. Reads `Library.scan_for()` from step
   3 to know which libraries to count.
5. `build_probe_profiles` fills in the metadata half of the same profiles,
   the Python and Django ranges and the declared dependencies. It reads
   only the PyPI columns we already hold, so it does not need a checkout
   and can run any time after a PyPI import; it is listed here because the
   profile is not complete without it.
6. `build_probe_catalog` rolls the finished profiles up into `ProbeSymbol`.
   Last, because it is a summary of everything above.

Steps 1 and 2 are the expensive ones and hold the only network calls. Steps
3 to 6 run against the database and the disk we already have, so they are
cheap to re-run and safe to repeat.

## build_probe_libraries

Records what each distribution is imported as, because PyPI does not publish
it. `pip install django-debug-toolbar` then `import debug_toolbar`;
djangorestframework imports as `rest_framework`, django-q2 as `django_q`. A
scan that guesses by swapping hyphens for underscores finds nothing for any
of those, and across the packages we have checkouts for, a guess is wrong
about half the time.

The import name is read out of the checkout we already cloned: the top-level
importable directories, preferring a package under `src/` over a loose script
at the root, and preferring a name that echoes the distribution. A package we
have no checkout for gets no row at all. It used to fall back to the guess and
label it `source=guess`, but a row nobody can tell from a read one once it is
in the table is worse than a missing row.

Set `scan` on a library to have scans count its usage too. It is nullable and
starts unset, which reads as off, because every library added is counted in
every file of every checkout. `django` ships toggled on.

```shell
docker compose run django uv run manage.py build_probe_libraries [--slug=<slug>] [--limit=<number>] [--min-score=<n>] [--differences-only] [--dry-run]
```

## build_probe_catalog

Rolls the scanned symbols, settings and patterns up into `ProbeSymbol`, one
row per library and name, with the counts replaced from the current profiles.

The curation on each row is left alone: a rebuild that quietly dropped a
deprecation would be worse than no catalogue at all. `deprecated`,
`deprecated_in`, `removed_in` and `notes` are ours to set, in the admin.
`--prune` drops rows nothing uses any more, except any row we have annotated.

```shell
docker compose run django uv run manage.py build_probe_catalog [--library=<name>] [--prune] [--dry-run]
```

## check_removals

Compares `probes/removals.py`, the table of what Django has removed, against
Django's own documentation: the deprecation timeline, plus any release notes
you name. Prints what the docs mention that the table does not have, sorted by
how many of our packages call it.

The table ships empty, so right now it prints everything. That is on purpose.
Two earlier attempts at filling it automatically both produced wrong rows:
inferring removals from whether a name still imports flagged two in five
names wrongly, and parsing the docs picks up the replacement names the same
bullets mention. A page that tells package authors their code calls a dead API
is worth being slow and right about, so rows get added by hand, either here or
by setting `removed_in` on a symbol in the admin.

It writes nothing.

```shell
docker compose run django uv run manage.py check_removals [--version=6.1]
```

## /probes/

An unlisted page at `/probes/` showing what the profiles add up to: the share
of packages supporting each Django and Python version, where those claims came
from, which libraries the source uses, the patterns, the settings read, the
APIs the running Django no longer has, and the declared dependencies. Long
tables are paginated, each on its own query parameter so paging one leaves the
others alone.

No login. Nothing on it is private, and a password would only stop us looking
at it, so it is kept out of the nav and the sitemap and marked noindex
instead. The roll-ups are full table scans, so each is cached for fifteen
minutes.

## scan_package_repos

Counts which Django APIs the checked out packages actually use, by parsing
their source rather than reading their metadata. Reads only what
`sync_package_repos` has already fetched and never touches the network.

Results are saved to the package's `PackageProbe` as `symbols`, a JSON list
of `{"symbol": "django.conf.settings", "count": 16}`, most used first, along
with `files_scanned`, `files_skipped`, the `commit` the tree was on and
`scanned_at`. It only writes the scan half, so the versions and dependencies
that `build_probe_profiles` filled in are left alone. Pass `--dry-run` to
report without saving.

`patterns` is the second half of the same parse: django-probe's named probes,
as `{"pattern": "probe:queryset_filter", "count": 12}`, most hit first. These
answer questions a dotted path cannot. `transaction.atomic` resolves to the
same symbol whether it was a decorator or a context manager, and a class
inheriting `AbstractUser` is a custom user model rather than a mention of a
name. The probes that ship today cover the queryset methods, `cache_page`,
`transaction.atomic`, `@receiver`, Django Tasks, a custom user model and
`AUTH_USER_MODEL`. Probe keys are `namespace:name`, so our own probes can be
registered under their own namespace rather than forking the package.

Setting names are kept rather than folded. `settings.AUTH_USER_MODEL` is
stored as `django.conf.settings.AUTH_USER_MODEL`, and the `settings_used`
property on the profile reads them back without the prefix. A setting Django
does not define, which is most of what a project invents, still folds onto the
bare `django.conf.settings`, so that count stays meaningful instead of turning
into an inventory of other people's naming habits.

This is the half that metadata cannot give you. `dj-twilio-sms` declares no
dependencies at all, yet its scan shows `ugettext_lazy`, `force_text` and
`django.utils.six`, all removed from Django years ago.

Counts are weighted by test suites, since tests import the most, which is why
the roll-up reports how many packages use a symbol alongside the raw total.

The counting comes from `django-probe`, which follows import aliasing, so
`from django.db import models` followed by `models.CharField` resolves to
`django.db.models.CharField` rather than being matched as text. A name in a
string or comment is not counted. `--package` takes any top-level import
name, so this is not limited to Django. With no `--package`, the scan counts
the libraries toggled on in `probes.Library`, falling back to `django`.

```shell
docker compose run django uv run manage.py scan_package_repos [--slug=<slug>] [--limit=<number>] [--package=<import-name>] [--top=<n>] [--totals-only]
```
