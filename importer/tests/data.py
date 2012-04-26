from django.contrib.auth.models import Group, User, Permission

from core.tests import datautil
from grid.models import Grid
from grid.models import Element, Feature, GridPackage
from package.models import Category, PackageExample, Package
from profiles.models import Profile


def load():

    group1, created = Group.objects.get_or_create(
        pk=1,
        name=u'Moderators',
    )
    group1.permissions.clear()
    group1.permissions = [
        Permission.objects.get(codename='delete_gridpackage'),
        Permission.objects.get(codename='delete_feature')
        ]

    user1, created = User.objects.get_or_create(
        pk=1,
        username=u'user',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=False,
        last_login=u'2010-01-01 12:00:00',
        password=u'sha1$644c9$347f3dd85fb609a5745ebe33d0791929bf08f22e',
        email='',
        date_joined=u'2010-01-01 12:00:00',
    )
    user2, created = User.objects.get_or_create(
        pk=2,
        username=u'cleaner',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=False,
        last_login=u'2010-01-01 12:00:00',
        #groups=[group1],
        password=u'sha1$e6fe2$78b744e21cddb39117997709218f4c6db4e91894',
        email='',
        date_joined=u'2010-01-01 12:00:00',
    )
    user2.groups = [group1]

    user3, created = User.objects.get_or_create(
        pk=3,
        username=u'staff',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=True,
        last_login=u'2010-01-01 12:00:00',
        password=u'sha1$8894d$c4814980edd6778f0ab1632c4270673c0fd40efe',
        email='',
        date_joined=u'2010-01-01 12:00:00',
    )
    user4, created = User.objects.get_or_create(
        pk=4,
        username=u'admin',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=True,
        is_staff=True,
        last_login=u'2010-01-01 12:00:00',
        password=u'sha1$52c7f$59b4f64ffca593e6abd23f90fd1f95cf71c367a4',
        email='',
        date_joined=u'2010-01-01 12:00:00',
    )

    for user in User.objects.all():
        Profile.objects.create(user=user)

    datautil.reset_sequences(Grid, Group, User, Permission, Category, PackageExample,
                             Package, Element, Feature, GridPackage)

