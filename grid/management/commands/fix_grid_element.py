from collections.abc import defaultdict

from django.core.management.base import BaseCommand
from grid.models import Element


class Command(BaseCommand):
    help = "fix Grid.Element table"

    def handle(self, *args, **kwargs):
        print("fixing Grid.Element table...")

        rows = Element.objects.all().values("grid_package_id", "feature_id", "id")

        dedup = defaultdict(list)

        for row in rows:
            dedup[(row["grid_package_id"], row["feature_id"])].append(row["id"])
        print("found {} duplicate rows...".format(len(rows) - len(dedup)))

        for (feature, package), ids in dedup.items():
            if inlist := sorted(ids)[1:]:
                print(
                    "deleting package {}, feature {} (id {})".format(
                        package, feature, ",".join(map(str, inlist))
                    )
                )
                Element.objects.filter(id__in=inlist).delete()
