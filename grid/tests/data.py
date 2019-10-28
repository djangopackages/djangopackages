from django.contrib.auth.models import Group, User, Permission

from core.tests import datautil
from grid.models import Grid
from grid.models import Element, Feature, GridPackage
from package.models import Category, PackageExample, Package
from profiles.models import Profile


def load():
    category, created = Category.objects.get_or_create(
        pk=1,
        slug='apps',
        title='App',
        description='Small components used to build projects.',
    )

    package1, created = Package.objects.get_or_create(
        pk=1,
        category=category,
        repo_watchers=0,
        title='Testability',
        pypi_url='',
        participants='malcomt,jacobian',
        pypi_downloads=0,
        repo_url='https://github.com/pydanny/django-la-facebook',

        repo_forks=0,
        slug='testability',
        repo_description='Increase your testing ability with this steroid free supplement.',
    )
    package2, created = Package.objects.get_or_create(
        pk=2,
        category=category,
        repo_watchers=0,
        title='Supertester',
        pypi_url='',
        participants='thetestman',
        pypi_downloads=0,
        repo_url='https://github.com/pydanny/django-uni-form',

        repo_forks=0,
        slug='supertester',
        repo_description='Test everything under the sun with one command!',
    )
    package3, created = Package.objects.get_or_create(
        pk=3,
        category=category,
        repo_watchers=0,
        title='Serious Testing',
        pypi_url='',
        participants='pydanny',
        pypi_downloads=0,
        repo_url='https://github.com/opencomparison/opencomparison',

        repo_forks=0,
        slug='serious-testing',
        repo_description='Make testing as painless as waxing your legs.',
    )
    package4, created = Package.objects.get_or_create(
        pk=4,
        category=category,
        repo_watchers=0,
        title='Another Test',
        pypi_url='',
        participants='pydanny',
        pypi_downloads=0,
        repo_url='https://github.com/djangopackages/djangopackages',

        repo_forks=0,
        slug='another-test',
        repo_description='Yet another test package, with no grid affiliation.',
    )

    grid1, created = Grid.objects.get_or_create(
        pk=1,
        description='A grid for testing.',
        title='Testing',
        is_locked=False,
        slug='testing',
    )
    grid2, created = Grid.objects.get_or_create(
        pk=2,
        description='Another grid for testing.',
        title='Another Testing',
        is_locked=False,
        slug='another-testing',
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
        title='Has tests?',
        grid=grid1,
        description='Does this package come with tests?',
    )
    feature2, created = Feature.objects.get_or_create(
        pk=2,
        title='Coolness?',
        grid=grid1,
        description='Is this package cool?',
    )

    element, created = Element.objects.get_or_create(
        pk=1,
        text='Yes',
        feature=feature1,
        grid_package=gridpackage1,
    )

    group1, created = Group.objects.get_or_create(
        pk=1,
        name='Moderators',
        #permissions=[[u'delete_gridpackage', u'grid', u'gridpackage'], [u'delete_feature', u'grid', u'feature']],
    )
    group1.permissions.clear()
    group1.permissions.set([
        Permission.objects.get(codename='delete_gridpackage'),
        Permission.objects.get(codename='delete_feature')
    ])

    user1, created = User.objects.get_or_create(
        pk=1,
        username='user',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=False,
        last_login='2010-01-01 12:00:00',
        email='',
        date_joined='2010-01-01 12:00:00',
    )
    user1.set_password('user')
    user1.save()

    user2, created = User.objects.get_or_create(
        pk=2,
        username='cleaner',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=False,
        last_login='2010-01-01 12:00:00',
        #groups=[group1],
        email='',
        date_joined='2010-01-01 12:00:00',
    )
    user2.set_password('cleaner')
    user2.save()

    user2.groups.set([group1])

    user3, created = User.objects.get_or_create(
        pk=3,
        username='staff',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=True,
        last_login='2010-01-01 12:00:00',
        email='',
        date_joined='2010-01-01 12:00:00',
    )
    user3.set_password('staff')
    user3.save()

    user4, created = User.objects.get_or_create(
        pk=4,
        username='admin',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=True,
        is_staff=True,
        last_login='2010-01-01 12:00:00',
        email='',
        date_joined='2010-01-01 12:00:00',
    )
    user4.set_password('admin')
    user4.save()

    packageexample, created = PackageExample.objects.get_or_create(
        pk=1,
        package=package1,
        url='http://www.example.com/',
        active=True,
        title='www.example.com',
    )
    for user in User.objects.all():
        profile = Profile.objects.create(user=user)

    datautil.reset_sequences(Grid, Group, User, Permission, Category, PackageExample,
                             Package, Element, Feature, GridPackage)

