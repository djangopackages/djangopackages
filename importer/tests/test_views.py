from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission

from grid.models import Grid, Element, Feature, GridPackage
from package.models import Package

from grid.tests import data


class TestImportGithub(TestCase):
    pass