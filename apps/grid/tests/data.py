from django.contrib.auth.models import Group, User, Permission

from core.tests import datautil
from grid.models import Grid
from grid.models import Element, Feature, GridPackage
from package.models import Category, PackageExample, Package
from profiles.models import Profile


def load():
    category, created = Category.objects.get_or_create(
        pk=1,
        slug=u'apps',
        title=u'App',
        description=u'Small components used to build projects.',
    )

    package1, created = Package.objects.get_or_create(
        pk=1,
        category=category,
        repo_watchers=0,
        title=u'Testability',
        pypi_url='',
        participants=u'malcomt,jacobian',
        pypi_downloads=0,
        repo_url=u'https://github.com/pydanny/django-la-facebook',
        repo_commits=0,
        repo_forks=0,
        slug=u'testability',
        repo_description=u'Increase your testing ability with this steroid free supplement.',
    )
    package2, created = Package.objects.get_or_create(
        pk=2,
        category=category,
        repo_watchers=0,
        title=u'Supertester',
        pypi_url='',
        participants=u'thetestman',
        pypi_downloads=0,
        repo_url=u'https://github.com/pydanny/django-uni-form',
        repo_commits=0,
        repo_forks=0,
        slug=u'supertester',
        repo_description=u'Test everything under the sun with one command!',
    )
    package3, created = Package.objects.get_or_create(
        pk=3,
        category=category,
        repo_watchers=0,
        title=u'Serious Testing',
        pypi_url='',
        participants=u'pydanny',
        pypi_downloads=0,
        repo_url=u'https://github.com/cartwheelweb/packaginator',
        repo_commits=0,
        repo_forks=0,
        slug=u'serious-testing',
        repo_description=u'Make testing as painless as waxing your legs.',
    )
    package4, created = Package.objects.get_or_create(
        pk=4,
        category=category,
        repo_watchers=0,
        title=u'Another Test',
        pypi_url='',
        participants=u'pydanny',
        pypi_downloads=0,
        repo_url=u'https://github.com/djangopackages/djangopackages',
        repo_commits=0,
        repo_forks=0,
        slug=u'another-test',
        repo_description=u'Yet another test package, with no grid affiliation.',
    )

    grid1, created = Grid.objects.get_or_create(
        pk=1,
        description=u'A grid for testing.',
        title=u'Testing',
        is_locked=False,
        slug=u'testing',
    )
    grid2, created = Grid.objects.get_or_create(
        pk=2,
        description=u'Another grid for testing.',
        title=u'Another Testing',
        is_locked=False,
        slug=u'another-testing',
    )

    gridpackage1, created = GridPackage.objects.get_or_create(
        pk=1,
        package=package1,
        grid=grid1,
    )
    gridpackage2, created = GridPackage.objects.get_or_create(
        pk=2,
        package=package1,
        grid=grid1,
    )
    gridpackage3, created = GridPackage.objects.get_or_create(
        pk=3,
        package=package3,
        grid=grid1,
    )
    gridpackage4, created = GridPackage.objects.get_or_create(
        pk=4,
        package=package3,
        grid=grid2,
    )
    gridpackage5, created = GridPackage.objects.get_or_create(
        pk=5,
        package=package2,
        grid=grid1,
    )

    feature1, created = Feature.objects.get_or_create(
        pk=1,
        title=u'Has tests?',
        grid=grid1,
        description=u'Does this package come with tests?',
    )
    feature2, created = Feature.objects.get_or_create(
        pk=2,
        title=u'Coolness?',
        grid=grid1,
        description=u'Is this package cool?',
    )

    element, created = Element.objects.get_or_create(
        pk=1,
        text=u'Yes',
        feature=feature1,
        grid_package=gridpackage1,
    )

    group1, created = Group.objects.get_or_create(
        pk=1,
        name=u'Moderators',
        #permissions=[[u'delete_gridpackage', u'grid', u'gridpackage'], [u'delete_feature', u'grid', u'feature']],
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

    packageexample, created = PackageExample.objects.get_or_create(
        pk=1,
        package=package1,
        url=u'http://www.example.com/',
        active=True,
        title=u'www.example.com',
    )
    for user in User.objects.all():
        profile = Profile.objects.create(user=user)

    datautil.reset_sequences(Grid, Group, User, Permission, Category, PackageExample,
                             Package, Element, Feature, GridPackage)

