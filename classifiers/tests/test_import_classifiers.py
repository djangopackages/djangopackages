from django.core.management import call_command
from classifiers.models import Classifier


def test_product_import(db, requests_mock):
    classifier_count = Classifier.objects.count()
    assert classifier_count == 0

    call_command("import_classifiers")

    assert Classifier.objects.count() > classifier_count
