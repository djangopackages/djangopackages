from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import RedirectView
from django.views.generic.edit import UpdateView
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.signals import user_logged_in

# from social_auth.signals import pre_update
# from social_auth.backends.contrib.github import GithubBackend

from profiles.forms import ProfileForm
from profiles.models import Profile


def profile_detail(request, github_account, template_name="profiles/profile.html"):

    # ugly fix on duplicated profile pages.
    # all of this should be migrated to be saved in the user model
    try:
        profile = get_object_or_404(Profile, github_account=github_account)
    except MultipleObjectsReturned:
        profile = Profile.objects.filter(github_account=github_account).latest('pk')

    return render(request, template_name,
        {"local_profile": profile, "user": profile.user},)


class ProfileEditUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "profiles/profile_edit.html"

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.INFO, "Profile Saved")
        return HttpResponseRedirect(reverse("profile_detail", kwargs={"github_account": self.get_object()}))


def github_user_update(sender, **kwargs):
    # import ipdb; ipdb.set_trace()
    try:
        user = kwargs['request'].user
    except (KeyError, AttributeError):
        user = kwargs.get('user')
    profile_instance, created = Profile.objects.get_or_create(user=user)
    profile_instance.github_account = user.username
    profile_instance.email = user.email
    profile_instance.save()
    return True

user_logged_in.connect(github_user_update)


class LogoutView(RedirectView):
    pattern_name = "home"

    def get_redirect_url(self, *args, **kwargs):
        logout(self.request)
        return super().get_redirect_url(*args, **kwargs)
