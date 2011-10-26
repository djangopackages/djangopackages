from django.conf.urls.defaults import *

from importer import views

urlpatterns = patterns("",

    url(
        regex   = r'^package$',
        view    = views.import_packages,
        name    = 'import_packages',
    ),  
)