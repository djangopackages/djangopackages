from django.db.models import Manager, Q, QuerySet

# TODO:
# - [ ] add search_index
# - [ ] add package (web/index)
# - [ ] add package pypi update
# - [ ] add package repos rescan


class PackageQuerySet(QuerySet):
    def active(self):
        return self.filter(
            Q(date_repo_archived__isnull=True)
            & Q(date_deprecated__isnull=True)
            & Q(deprecated_by__isnull=True)
            # Q(deprecates_package__isnull=True)
        )

    def archived(self):
        return self.exclude(date_repo_archived__isnull=True)

    def deprecated(self):
        return self.exclude(
            Q(date_deprecated__isnull=True),
            Q(deprecated_by__isnull=True),
            # Q(deprecates_package__isnull=True),
        )

    def supports_python3(self):
        return self.filter(supports_python3=True)


class PackageManager(Manager):
    def get_queryset(self):
        return PackageQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def archived(self):
        return self.get_queryset().archived()

    def deprecated(self):
        return self.get_queryset().deprecated()

    def supports_python3(self):
        return self.get_queryset().supports_python3()
