import datetime

import pytest
from django.utils.timezone import make_aware
from model_bakery import baker

from package.models import Category, Commit, Package, PackageExample, Version


@pytest.fixture(autouse=True)
def set_time(time_machine):
    time_machine.move_to(make_aware(datetime.datetime(2022, 2, 20, 2, 22)))
    yield


@pytest.fixture()
def category(db) -> Category:
    return baker.make(Category)


@pytest.fixture()
def commit(db, package) -> Commit:
    return baker.make(Commit, package=package)


@pytest.fixture()
def package_bitbucket(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://bitbucket.org/Manfre/django-mssql/",
        slug="django-mssql",
        title="django-mssql",
    )


@pytest.fixture()
def package_gitlab(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://gitlab.com/lansharkconsulting/django/django-encrypted-model-fields",
        slug="django-encrypted-model-fields",
        title="django-encrypted-model-fields",
    )


@pytest.fixture()
def package_gitlab_archived(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://gitlab.com/jeff.triplett/django-metadata",
        slug="django-metadata",
        title="django-metadata",
    )


@pytest.fixture()
def package_gitlab_invalid(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://gitlab.com/jeff.triplett/does-not-exist",
        slug="does-not-exist",
        title="does-not-exist",
    )


@pytest.fixture()
def package(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://github.com/django/deps",
        slug="deps",
        title="Django Enhancement Proposals",
    )


@pytest.fixture()
def package_archived(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://github.com/pydanny/dj-paginator",
        slug="dj-paginator",
        title="dj-paginator",
    )


@pytest.fixture()
def package_invalid(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://github.com/djangopackages/does-not-exist",
        slug="invldpkg",
        title="Invalid Package",
    )


@pytest.fixture()
def package_example(db, package) -> PackageExample:
    return baker.make(PackageExample, package=package)


@pytest.fixture()
def package_codeberg(db, category) -> Package:
    return baker.make(
        Package,
        category=category,
        repo_url="https://codeberg.org/timo_sams/djangopackages-test",
        slug="codeberg-djangopackages-test",
        title="codeberg-djangopackages-test",
    )


@pytest.fixture()
def version(db, package) -> Version:
    return baker.make(Version, package=package)


@pytest.fixture()
def package_abandoned(db, category) -> Package:
    package = baker.make(
        Package,
        category=category,
        title="Abandoned Package",
        created_by=None,
        repo_watchers=1000,
        pypi_downloads=26257,
        last_modified_by=None,
        repo_url="https://github.com/divio/django-divioadmin",
        repo_forks=1000,
        slug="django-divioadmin",
        repo_description="not maintained anymore.",
    )
    baker.make(
        Commit,
        package=package,
        commit_date=make_aware(datetime.datetime(2020, 2, 19, 0, 0)),
        commit_hash="2b54b0ae95ef805c07ca3c0b9c5184466b65c55b",
    )
    return package


@pytest.fixture()
def package_abandoned_ten_years(db, category) -> Package:
    package = baker.make(
        Package,
        category=category,
        title="Abandoned Package 10 years",
        created_by=None,
        repo_watchers=1000,
        pypi_downloads=26257,
        last_modified_by=None,
        repo_url="https://github.com/divio/django-divioadmin2",
        repo_forks=1000,
        slug="django-divioadmin2",
        repo_description="not maintained anymore.",
    )
    baker.make(
        Commit,
        package=package,
        commit_date=make_aware(datetime.datetime(2012, 2, 19, 0, 0)),
        commit_hash="2b54b0ae95ef805c07ca3c0b9c5184466b65c66c",
    )
    return package


@pytest.fixture()
def package_cms(db, category) -> Package:
    package = baker.make(
        Package,
        category=category,
        title="Django CMS",
        slug="django-cms",
        repo_watchers=967,
        pypi_url="https://pypi.org/project/django-cms/",
        pypi_downloads=26257,
        repo_url="https://github.com/divio/django-cms",
        participants="chrisglass,digi604,erobit,fivethreeo,ojii,stefanfoulis,pcicman,DrMeers,brightwhitefox,FlashJunior,philomat,jezdez,havan,acdha,m000,hedberg,piquadrat,spookylukey,izimobil,ulope,emiquelito,aaloy,lasarux,yohanboniface,aparo,jsma,johbo,ionelmc,quattromic,almost,specialunderwear,mitar,yml,pajusmar,diofeher,marcor,cortextual,hysia,dstufft,ssteinerx,oversize,jalaziz,tercerojista,eallik,f4nt,kaapa,mbrochh,srj55,dz,mathijs-dumon,sealibora,cyberj,adsworth,tokibito,DaNmarner,IanLewis,indexofire,bneijt,tehfink,PPvG,seyhunak,pigletto,fcurella,gleb-chipiga,beshrkayali,kinea,lucasvo,jordanjambazov,tonnzor,centralniak,arthur-debert,bzed,jasondavies,nimnull,limpbrains,pvanderlinden,sleytr,sublimevelo,netpastor,dtt101,fkazimierczak,merlex,mrlundis,restless,eged,shanx,ptoal",
        repo_forks=283,
        repo_description="An Advanced Django CMS.",
    )

    baker.make(
        Version,
        license="BSD License",
        downloads=13644,
        package=package,
        number="2.1.0.beta3",
        hidden=False,
        supports_python3=True,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=4326,
        package=package,
        number="2.0.2",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=212,
        package=package,
        number="2.0.1",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=1062,
        package=package,
        number="2.0.0",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=299,
        package=package,
        number="2.1.0.rc1",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=726,
        package=package,
        number="2.1.0.rc2",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=850,
        package=package,
        number="2.1.0.rc3",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=1613,
        package=package,
        number="2.1.0",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=906,
        package=package,
        number="2.1.1",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=715,
        package=package,
        number="2.1.2",
        hidden=False,
    )
    baker.make(
        Version,
        license="BSD License",
        downloads=1904,
        package=package,
        number="2.1.3",
        hidden=False,
    )

    return package
