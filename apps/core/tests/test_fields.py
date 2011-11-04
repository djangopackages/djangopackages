from django.test import TestCase

from core.fields import CreationDateTimeField, ModificationDateTimeField

class TestFields(TestCase):

    def test_create_override(self):
        field = CreationDateTimeField()
        triple = field.south_field_triple()

        self.assertEquals(triple[0], 'django.db.models.fields.DateTimeField')
        self.assertEquals(triple[1], list())
        self.assertEquals(triple[2], {'default': 'datetime.datetime.now', 'blank': 'True'})

    def test_modify_override(self):
        field = ModificationDateTimeField()
        triple = field.south_field_triple()

        self.assertEquals(triple[0], 'django.db.models.fields.DateTimeField')
        self.assertEquals(triple[1], list())
        self.assertEquals(triple[2], {'default': 'datetime.datetime.now', 'blank': 'True'})
