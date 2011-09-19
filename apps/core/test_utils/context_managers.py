# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import get_language, activate
from shutil import rmtree as _rmtree
from tempfile import template, mkdtemp, _exists

class NULL:
    pass

class SettingsOverride(object):
    """
    Overrides Django settings within a context and resets them to their inital
    values on exit.
    
    Example::
    
        with SettingsOverride(DEBUG=True):
            # do something
    """
    
    def __init__(self, **overrides):
        self.overrides = overrides
        
    def __enter__(self):
        self.old = {}
        for key, value in self.overrides.items():
            self.old[key] = getattr(settings, key, NULL)
            setattr(settings, key, value)
        
    def __exit__(self, type, value, traceback):
        for key, value in self.old.items():
            if value is not NULL:
                setattr(settings, key, value)
            else:
                delattr(settings,key) # do not pollute the context!


class LanguageOverride(object):
    def __init__(self, language):
        self.newlang = language
        
    def __enter__(self):
        self.oldlang = get_language()
        activate(self.newlang)
        
    def __exit__(self, type, value, traceback):
        activate(self.oldlang)


class TemporaryDirectory:
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example::

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everthing contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix=template, dir=None):
        self.name = mkdtemp(suffix, prefix, dir)

    def __enter__(self):
        return self.name

    def cleanup(self):
        if _exists(self.name):
            _rmtree(self.name)

    def __exit__(self, exc, value, tb):
        self.cleanup()


class ChangeModel(object):
    """
    Changes attributes on a model while within the context.
    
    These changes *ARE* saved to the database for the context!
    """
    def __init__(self, instance, **overrides):
        self.instance = instance
        self.overrides = overrides
        
    def __enter__(self):
        self.old = {}
        for key, value in self.overrides.items():
            self.old[key] = getattr(self.instance, key, NULL)
            setattr(self.instance, key, value)
        self.instance.save()
        
    def __exit__(self, exc, value, tb):
        for key in self.overrides.keys():
            old_value = self.old[key]
            if old_value is NULL:
                delattr(self.instance, key)
            else:
                setattr(self.instance, key, old_value)
        self.instance.save()
