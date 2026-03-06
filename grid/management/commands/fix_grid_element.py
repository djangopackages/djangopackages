import logging
from collections.abc import defaultdict

from django.core.management.base import BaseCommand

from grid.models import Element

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Removes duplicate Element objects"

    def handle(self, *args, **kwargs):
        logger.info("fixing Grid.Element table...")

        rows = Element.objects.all().values("grid_package_id", "feature_id", "id")

        dedup = defaultdict(list)

        for row in rows:
            dedup[(row["grid_package_id"], row["feature_id"])].append(row["id"])
        logger.info(f"found {len(rows) - len(dedup)} duplicate rows...")

        for (feature, package), ids in dedup.items():
            if inlist := sorted(ids)[1:]:
                logger.info(
                    "deleting package {}, feature {} (id {})".format(
                        package, feature, ",".join(map(str, inlist))
                    )
                )
                Element.objects.filter(id__in=inlist).delete()
