from django.contrib.auth.models import Group, Permission, User

from package.models import Category, Package

def make():
    
    create_users()
    
    category, created = Category.objects.get_or_create(
        title="App",
        slug="apps",
        description="Small components used to build projects."
    )
    category.save()
    
    package, created = Package.objects.get_or_create(
        category = category,
        participants = "malcomt,jacobian",
        repo_description = "Increase your testing ability with this steroid free supplement.",
        repo_url = "https://github.com/pydanny/django-la-facebook",
        slug = "testability",
        title="Testability"
    )
    package.save()
    package, created = Package.objects.get_or_create(
        category = category,
        participants = "thetestman",
        repo_description = "Test everything under the sun with one command!",
        repo_url = "https://github.com/pydanny/django-uni-form",
        slug = "supertester",
        title="Supertester"
    )
    package.save()
    package, created = Package.objects.get_or_create(
        category = category,
        participants = "pydanny",
        repo_description = "Make testing as painless as waxing your legs.",
        repo_url = "https://github.com/cartwheelweb/packaginator",
        slug = "serious-testing",
        title="Serious Testing"
    )
    package.save()    
    package, created = Package.objects.get_or_create(
        category = category,
        participants = "pydanny",
        repo_description = "Yet another test package, with no grid affiliation.",
        repo_url = "https://github.com/djangopackages/djangopackages",
        slug = "another-test",
        title="Another Test"
    )
    package.save()
    
def create_users():
    
    user = User.objects.create_user(
        username="user",
        password="user",
        email="user@example.com"
    )
    user.is_active = True
    user.save()
    
    user = User.objects.create_user(
        username="cleaner",
        password="cleaner",
        email="cleaner@example.com"
    )
    user.is_active = True    
    user.save()

    user = User.objects.create_user(
        username="staff",
        password="staff",
        email="staff@example.com"
    )
    user.is_active = True
    user.is_staff = True
    user.save()
    
    user = User.objects.create_user(
        username="admin",
        password="admin",
        email="admin@example.com"
    )
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True    
    user.save()    

    """
    perm1 = Permission.objects.create(codename='delete_gridpackage',
            content_type__app_label='grid')    
    perm1.save()

    perm2 = Permission.objects.create(codename='delete_feature',
            content_type__app_label='grid')    
    perm2.save()


    group = Group.objects.create(
        name = "Moderators",
    )
    group.save()
    """