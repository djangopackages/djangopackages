from django.conf.urls.defaults import *
from django.db.models import Count
from django.views.generic.list_detail import object_detail, object_list
from django.views.generic.date_based import archive_index
from django.views.generic.simple import direct_to_template

from profiles import views


urlpatterns = patterns("",
	url(r"^edit/$", views.profile_edit, name="profile_edit"),    
	url(r"^$", views.profile_list, name="profile_list"),    	
	url(r"^(?P<github_account>[-\w]+)$", views.profile_detail, name="profile_detail"),

)