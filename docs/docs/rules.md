## Single Rule Logic

`Package.score` is the sum of the six point rules below (not deprecated or archived, description, PyPI downloads, forks, people using or favoriting it, stars), 20 points each, scaled to 0 to 100 and then multiplied by the activity factor (`searchv3.rules.score_package`). Usage and favorites share one rule, `UsageCountRule`: each count is log scaled and the higher of the two is the score, with a floor of one point for any package active in the last three years. The grids sort on it and show packages at or above `PACKAGE_SCORE_MIN` in their comparison tables, the search index weights packages by it, and the Package Score page on each package lists the rules with the points earned.

The **activity factor** fades the score with time since the package last shipped. The date is the latest PyPI release for a package on PyPI; commits do not count for a released package, since a project that commits but never ships is not maintained in any way its users can install. A package that is not on PyPI (no PyPI link, as for deployable apps and project templates) is dated by its latest commit instead. The factor is 1.0 for a year after that date, then halves every eighteen months: two and a half years idle keeps half the points, five years a sixth, ten years about 1%. A package with no date on record scores 0. An ageing package drifts down its grids and out of the comparison table rather than vanishing on a birthday, stays on the full package lists and in search with its page saying when it last shipped, and comes back with the next release. The factor is computed from dates on every score run, never set by hand.

### ::: searchv3.rules.ActivityRule


### ::: searchv3.rules.DeprecatedRule


### ::: searchv3.rules.DescriptionRule


### ::: searchv3.rules.DownloadsRule


### ::: searchv3.rules.ForkRule


### ::: searchv3.rules.UsageCountRule


### ::: searchv3.rules.WatchersRule


### ::: searchv3.rules.DocumentationRule


## Group Rule Logic

### ::: searchv3.rules.ScoreRuleGroup
