## Single Rule Logic

`Package.score` is the sum of the eight point rules below, 20 points each, scaled to 0 to 100 (`searchv3.rules.score_package`). The grids sort on it and show packages at or above `PACKAGE_SCORE_MIN` in their comparison tables, the search index weights packages by it, and the Package Score page on each package lists the rules with the points earned.

One rule is a gate instead of points. A **dormant** package, one whose latest PyPI release is three or more years old, scores 0 whatever else it has. Commits do not keep a released package awake. A package with no release on record is judged on its latest commit instead, and one with no dates at all is dormant. It stays listed on its grids' full package lists and in search, with its page saying when it last shipped, and it leaves the comparison tables. Dormancy is computed from dates on every score run, never set by hand, and clears itself with the next release.

### ::: searchv3.rules.DormantRule


### ::: searchv3.rules.DeprecatedRule


### ::: searchv3.rules.DescriptionRule


### ::: searchv3.rules.DownloadsRule


### ::: searchv3.rules.ForkRule


### ::: searchv3.rules.UsageCountRule


### ::: searchv3.rules.WatchersRule


### ::: searchv3.rules.FavoritePackageRule


### ::: searchv3.rules.DocumentationRule


### ::: searchv3.rules.RecentReleaseRule


## Group Rule Logic

### ::: searchv3.rules.ScoreRuleGroup
