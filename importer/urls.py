from django.conf.urls.defaults import patterns, url

from importer import views

urlpatterns = patterns("",

    url(
        regex   = r'^github/$',
        view    = views.import_github,
        name    = 'import_github',
    ),
)