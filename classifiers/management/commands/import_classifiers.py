import djclick as click
import structlog

from rich import print
from trove_classifiers import classifiers as trove_classifiers

from classifiers.models import Classifier


ALLOW_LIST = [
    "Development Status",
    "Framework :: Celery",
    "Framework :: Django",
    "Framework :: Django CMS",
    "Framework :: Wagtail",
    "License",
    "Programming Language :: Python",
]

log = structlog.get_logger(__name__)


@click.command()
def command():
    print("[yellow]import_classifiers[/yellow]")

    for trove_classifier in sorted(trove_classifiers):
        log.info(trove_classifier=trove_classifier)
        print(trove_classifier)

        active = any(
            [allow for allow in ALLOW_LIST if trove_classifier.startswith(allow)]
        )
        if active:
            tags = [tag.strip() for tag in trove_classifier.split("::")]
        else:
            tags = None

        classifier, created = Classifier.objects.update_or_create(
            classifier=trove_classifier, defaults={"active": active, "tags": tags}
        )
