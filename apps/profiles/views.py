from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from uni_form.helpers import FormHelper, Submit, HTML
from uni_form.layout import Layout, Fieldset, ButtonHolder

from social_auth.signals import pre_update
from social_auth.backends.contrib.github import GithubBackend

from profiles.forms import ProfileForm
from profiles.models import Profile

def profile_detail(request, github_account, template_name="profiles/profile.html"):

    profile = get_object_or_404(Profile, github_account=github_account)

    return render(request, template_name,
        {"local_profile": profile, "user":profile.user},)

def profile_list(request, template_name="profiles/profiles.html"):

    if request.user.is_staff:
        users = User.objects.all()
    else:
        users = User.objects.filter(is_active=True)

    return render(request, template_name,
        {
            "users": users
        })

@login_required
def profile_edit(request, template_name="profiles/profile_edit.html"):

    profile = request.user.get_profile()
    form = ProfileForm(request.POST or None, instance=profile)

    if form.is_valid():
        form.save()
        msg = 'Profile edited'
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(reverse("profile_detail", kwargs={"github_account":profile.github_account }))
        
    # TODO - move this to a template
    github_account = """
    <div 
        id="div_id_github_account" 
        class="ctrlHolder"><label for="id_github_account" >Github account</label><strong>{0}</strong></div>
    """.format(profile.github_account)
        
    helper = FormHelper()
    helper.form_class = "profile-edit-form"
    helper.layout = Layout(
        Fieldset(
            '',
            HTML(github_account),
            'bitbucket_url',
            'google_code_url',
        ),
        ButtonHolder(
            Submit('edit', 'Edit', css_class="awesome forestgreen"),
        )
    )        

    return render(request, template_name,
        {
            "profile": profile,
            "form": form,
            "helper":helper,
        })

def github_user_update(sender, user, response, details, **kwargs):
    profile_instance, created = Profile.objects.get_or_create(user=user)
    profile_instance.github_account = details['username']
    profile_instance.email = details['email']
    profile_instance.save()
    return True

pre_update.connect(github_user_update, sender=GithubBackend)

