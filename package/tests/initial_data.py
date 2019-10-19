from grid.models import Grid
from django.contrib.auth.models import Group, User, Permission
from package.models import Category, PackageExample, Package
from grid.models import Element, Feature, GridPackage
from core.tests import datautil


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

    # password is 'user'
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
        password='pbkdf2_sha256$36000$Hp59Lym7JZyI$GVsyeRLCloSj4xI/1F5qf9dIZ2KF/ApMZFun7tiAxuc=',
        email='',
        date_joined='2010-01-01 12:00:00',
    )
    user2.groups.set([group1])
    user2.set_password('cleaner')
    user2.save()

    user3, created = User.objects.get_or_create(
        pk=3,
        username='staff',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=False,
        is_staff=True,
        last_login='2010-01-01 12:00:00',
        password='pbkdf2_sha256$36000$4Ytv7EOqXyNl$Wsnq1GncbyYDUQ5ieQIEBCsoolNWLcApXChKYS5Us4I=',
        email='',
        date_joined='2010-01-01 12:00:00',
    )
    user3.set_password('staff')
    user3.save()

    # password is 'admin'
    user4, created = User.objects.get_or_create(
        pk=4,
        username='admin',
        first_name='',
        last_name='',
        is_active=True,
        is_superuser=True,
        is_staff=True,
        last_login='2010-01-01 12:00:00',
        password='pbkdf2_sha256$36000$HizLkJV9vzk4$++1pBxJlH/uqIn5Qx0jugTH1b3U5SyZTaqnm+kSk7pQ=',
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

    packageexample2, created = PackageExample.objects.get_or_create(
        pk=2,
        package=package1,
        url=u'http://my.example.com/',
        active=True,
        title=u'my.example.com',
        created_by=user1,
    )

    packageexample3, created = PackageExample.objects.get_or_create(
        pk=3,
        package=package1,
        url=u'http://other.example.com/',
        active=True,
        title=u'other.example.com',
        created_by=user2,
    )

    datautil.reset_sequences(Grid, Group, User, Permission, Category, PackageExample,
                             Package, Element, Feature, GridPackage)
