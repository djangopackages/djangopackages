from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext


def profile_detail(request, username, template_name="idios/profile.html"):
	""" TODO - fix template """

	return render_to_response(template_name,
	{},


	RequestContext(request))