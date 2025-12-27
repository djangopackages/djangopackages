from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, RedirectView, DetailView
from django.views.generic.edit import UpdateView
from django.utils.translation import gettext_lazy as _

from package.models import Package
from profiles.forms import ProfileForm, ExtraFieldFormSet
from profiles.models import Profile, ExtraField

# from social_auth.signals import pre_update
# from social_auth.backends.contrib.github import GithubBackend


class ProfileDetailView(DetailView):
    model = Profile
    template_name = "new/profile_detail.html"
    slug_url_kwarg = "github_account"
    slug_field = "github_account"
    context_object_name = "local_profile"

    def get_queryset(self):
        return super().get_queryset().select_related("user")

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset().select_related("user")

        github_account = self.kwargs.get(self.slug_url_kwarg)
        try:
            return queryset.get(github_account=github_account)
        except MultipleObjectsReturned:
            return queryset.filter(github_account=github_account).latest("pk")
        except Profile.DoesNotExist:
            raise Http404("No profile found matching the query")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.object
        context["profile"] = profile
        context["user"] = profile.user
        context["extra_fields"] = ExtraField.objects.filter(profile=profile)
        context["self_profile"] = (
            self.request.user.is_authenticated and self.request.user == profile.user
        )
        return context


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


class ProfilePackageBaseView(ListView):
    model = Package
    context_object_name = "packages"
    paginate_by = 10

    def get_template_names(self):
        if self.request.headers.get("HX-Target") == self.target_id:
            return ["new/partials/profile_packages_table.html"]
        return ["new/partials/profile_packages_card.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.profile
        context["htmx_url"] = self.htmx_url
        context["target_id"] = self.target_id
        context["card_title"] = self.card_title
        context["card_icon"] = self.card_icon
        return context


class ProfileContributedPackagesView(ProfilePackageBaseView):
    target_id = "contributed-packages-table-container"
    htmx_url = "profile_contributed_packages"
    card_title = _("Packages Contributed To")
    card_icon = "ph-package"

    def get_queryset(self):
        self.profile = get_object_or_404(
            Profile.objects.filter(github_account=self.kwargs.get("github_account"))
        )
        return self.profile.my_packages()


class ProfileFavoritePackagesView(ProfilePackageBaseView):
    target_id = "favorite-packages-table-container"
    htmx_url = "profile_favorite_packages"
    card_title = _("Favorite Packages")
    card_icon = "ph-heart"

    def get_queryset(self):
        self.profile = get_object_or_404(
            Profile.objects.filter(
                user__is_active=True, github_account=self.kwargs.get("github_account")
            ).select_related("user")
        )
        if not self.profile.share_favorites and self.request.user != self.profile.user:
            raise PermissionDenied
        return Package.objects.filter(favorite__favorited_by=self.profile.user)
