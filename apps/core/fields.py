from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField

class CreationDateTimeField(CreationDateTimeField):

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.DateTimeField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)    
        
        
class ModificationDateTimeField(ModificationDateTimeField):

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.DateTimeField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)