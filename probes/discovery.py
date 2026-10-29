"""Find packages on PyPI by trove classifier, with or without a date range.

None of the APIs we already use can answer "what was uploaded with a
`Framework :: Wagtail` classifier this week". pypistats takes one
package name at a time, PyPI's JSON API gives classifiers per package,
and the web search is HTML. The public BigQuery dataset
`bigquery-public-data.pypi.distribution_metadata` has one row per
uploaded file with its classifiers and upload time, which turns the
question into a query.

What comes back is a review list, split into packages we already track
and ones new to us. Nothing here creates a package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings

from probes.awesome import package_index
from probes.imports import canonical_name

TABLE = "`bigquery-public-data.pypi.distribution_metadata`"

# Framework name on the command line -> classifier prefix. Checked against
# the upstream trove list on 2026-10-27: these are the only Django-related
# `Framework ::` families. There is none for DRF, Channels or Ninja.
FRAMEWORKS = {
    "django": "Framework :: Django",
    "wagtail": "Framework :: Wagtail",
    "django-cms": "Framework :: Django CMS",
}


@dataclass(frozen=True)
class Discovered:
    name: str
    first_upload: datetime
    last_upload: datetime
    version: str
    home_page: str
    summary: str

    @property
    def pypi_url(self) -> str:
        return f"https://pypi.org/project/{self.name}/"


@dataclass
class Discovery:
    tracked: list[tuple[Discovered, int]]  # with the Package pk
    new: list[Discovered]
    bytes_processed: int = 0


def build_query(framework: str, days: int | None) -> tuple[str, dict]:
    """The SQL and its parameters. `days=None` means the whole index.

    One row per project. The classifier match is a prefix so the bare
    `Framework :: Django` and every `Framework :: Django :: 5.2` both
    count. BigQuery prunes this table by `upload_time`: measured on
    2026-10-29, seven days scanned 0.23 GB against 9 GB for the whole
    index, so the date filter is what keeps the feed cheap.
    """
    prefix = FRAMEWORKS[framework]
    where = [
        "EXISTS (SELECT 1 FROM UNNEST(classifiers) c WHERE STARTS_WITH(c, @prefix))"
    ]
    params = {"prefix": prefix}
    if days is not None:
        where.append(
            "upload_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)"
        )
        params["days"] = days
    sql = f"""
SELECT
  name,
  MIN(upload_time) AS first_upload,
  MAX(upload_time) AS last_upload,
  ARRAY_AGG(version ORDER BY upload_time DESC LIMIT 1)[OFFSET(0)] AS version,
  ARRAY_AGG(home_page ORDER BY upload_time DESC LIMIT 1)[OFFSET(0)] AS home_page,
  ARRAY_AGG(summary ORDER BY upload_time DESC LIMIT 1)[OFFSET(0)] AS summary
FROM {TABLE}
WHERE {" AND ".join(where)}
GROUP BY name
ORDER BY last_upload DESC
""".strip()
    return sql, params


def bigquery_client():
    """A client from the service account JSON in settings.

    Imported here so the rest of the site never pays for the Google SDK
    at startup, and so tests can hand in a fake without the key.
    """
    from google.cloud import bigquery
    from google.oauth2 import service_account

    raw = settings.GOOGLE_BIGQUERY_CREDENTIALS
    if not raw:
        raise RuntimeError(
            "GOOGLE_BIGQUERY_CREDENTIALS is not set. See docs/management_commands.md."
        )
    info = json.loads(raw)
    credentials = service_account.Credentials.from_service_account_info(info)
    return bigquery.Client(project=credentials.project_id, credentials=credentials)


def _job_config(params: dict, *, dry_run: bool):
    from google.cloud import bigquery

    query_parameters = [
        bigquery.ScalarQueryParameter(
            key, "INT64" if isinstance(value, int) else "STRING", value
        )
        for key, value in params.items()
    ]
    return bigquery.QueryJobConfig(
        query_parameters=query_parameters,
        maximum_bytes_billed=settings.GOOGLE_BIGQUERY_MAX_BYTES_BILLED,
        dry_run=dry_run,
        use_query_cache=True,
    )


def estimate(framework: str, days: int | None, *, client=None) -> int:
    """Bytes the query would scan, without running it. Costs nothing."""
    sql, params = build_query(framework, days)
    client = client or bigquery_client()
    job = client.query(sql, job_config=_job_config(params, dry_run=True))
    return job.total_bytes_processed


def discover(framework: str, days: int | None, *, client=None) -> Discovery:
    """Run the query and split the rows by whether we already index them."""
    sql, params = build_query(framework, days)
    client = client or bigquery_client()
    job = client.query(sql, job_config=_job_config(params, dry_run=False))
    rows = [
        Discovered(
            name=row["name"],
            first_upload=row["first_upload"],
            last_upload=row["last_upload"],
            version=row["version"] or "",
            home_page=row["home_page"] or "",
            summary=row["summary"] or "",
        )
        for row in job.result()
    ]
    return split(rows, bytes_processed=job.total_bytes_processed or 0)


def split(rows: list[Discovered], *, bytes_processed: int = 0) -> Discovery:
    """Which of these are packages we already have, by PyPI name."""
    _, by_pypi = package_index()
    tracked, new = [], []
    for row in rows:
        pk = by_pypi.get(canonical_name(row.name))
        if pk is None:
            new.append(row)
        else:
            tracked.append((row, pk))
    return Discovery(tracked=tracked, new=new, bytes_processed=bytes_processed)
