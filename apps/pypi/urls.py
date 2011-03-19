from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list

from pypi.models import PypiUpdateLog

urlpatterns = patterns("",

    url(
        regex   = r"^$",
        view    = object_list,
        name    = "pypi_history",
        kwargs  = {
            "queryset": PypiUpdateLog.objects.all()
        }
    ),
)