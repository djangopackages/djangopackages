from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from uni_form.helpers import FormHelper, Submit, Reset

from profiles.forms import ProfileForm
from profiles.models import Profile

def profile_detail(request, username, template_name="idios/profile.html"):
	""" TODO - fix template """

	return render_to_response(template_name,
	{},


	RequestContext(request))
	
@login_required
def profile_edit(request, template_name="profiles/profile_edit.html"):

    helper = FormHelper()
    submit = Submit('edit','Edit')
    helper.add_input(submit) 
    reset = Reset('reset','Reset')    
    helper.add_input(reset)        

    profile = get_object_or_404(Profile, user=request.user)
    form = ProfileForm(request.POST or None, instance=profile)


    if form.is_valid():
        form.save()
        msg = 'Profile edited'
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(reverse("profile_detail", kwargs={"username":profile.user.username }))

    return render_to_response(template_name,
        {
            "profile": profile,
            "form": form,
            "helper":helper,
        },
        context_instance=RequestContext(request)
    )
