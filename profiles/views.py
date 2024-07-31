from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import MultipleObjectsReturned
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import RedirectView
from django.views.generic.edit import UpdateView

from package.models import Package
from profiles.forms import ProfileForm, ExtraFieldFormSet
from profiles.models import Profile, ExtraField

# from social_auth.signals import pre_update
# from social_auth.backends.contrib.github import GithubBackend


def profile_detail(request, github_account, template_name="profiles/profile.html"):
    # ugly fix on duplicated profile pages.
    # all of this should be migrated to be saved in the user model
    try:
        profile = get_object_or_404(Profile, github_account=github_account)
    except MultipleObjectsReturned:
        profile = Profile.objects.filter(github_account=github_account).latest("pk")

    extra_fields = ExtraField.objects.filter(profile=profile)

    context = {
        "local_profile": profile,
        "user": profile.user,
        "extra_fields": extra_fields,
    }
    if profile.share_favorites:
        context["favorite_packages"] = Package.objects.filter(
            favorite__favorited_by=profile.user
        )[:25]

    return render(request, template_name, context)


class ProfileEditUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "profiles/profile_edit.html"

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["extra_fields_formset"] = ExtraFieldFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["extra_fields_formset"] = ExtraFieldFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["extra_fields_formset"]
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.add_message(self.request, messages.INFO, "Profile Saved")
            return HttpResponseRedirect(
                reverse("profile_detail", kwargs={"github_account": self.get_object()})
            )
        else:
            messages.add_message(
                self.request, messages.ERROR, "There are errors in the form"
            )
            context["form"] = form
            context["extra_fields_formset"] = formset
            return self.render_to_response(context)


def github_user_update(sender, **kwargs):
    # import ipdb; ipdb.set_trace()
    try:
        user = kwargs["request"].user
    except (KeyError, AttributeError):
        user = kwargs.get("user")
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
