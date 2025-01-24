from django.utils.timezone import now
from model_bakery import baker

from searchv2.models import SearchV2


def test_searchv2_create(db):
    baker.make(
        SearchV2,
        item_type="package",
        title="Django Uni-Form",
        title_no_prefix="uni-form",
        slug="django-uni-form",
        slug_no_prefix="uni-form",
        clean_title="uniform",
        description="Blah blah blah",
        category="app",
        absolute_url="/packages/p/django-uni-form/",
        repo_watchers=500,
        repo_forks=85,
        score=600,
        pypi_downloads=30000,
        participants="pydanny,maraujop,et,al",
        last_committed=now(),
        last_released=now(),
    )
    assert SearchV2.objects.count() == 1
