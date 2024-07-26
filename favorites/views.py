from django.views.generic import View
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django_htmx.http import HttpResponseClientRedirect
from package.models import Package
from favorites.models import Favorite


class FavoritePackage(View):
    def post(self, request, id):
        if not request.user.is_authenticated:
            return HttpResponseClientRedirect(settings.LOGIN_URL)

        try:
            package = Package.objects.get(id=id)
        except Package.DoesNotExist:
            messages.error(request, "Package does not exist")
            return HttpResponseClientRedirect("/")

        _, created = Favorite.objects.get_or_create(
            package=package, favorited_by=request.user
        )
        return render(
            request,
            "package/partials/favorites.html#unfavorite_btn",
            {"package": package},
        )


class UnFavoritePackage(View):
    def post(self, request, id):
        if not request.user.is_authenticated:
            return HttpResponseClientRedirect(settings.LOGIN_URL)

        try:
            package = Package.objects.get(id=id)
        except Package.DoesNotExist:
            messages.error(request, "Package does not exist")
            return HttpResponseClientRedirect("/")
        Favorite.objects.get(package=package, favorited_by=request.user).delete()
        return render(
            request,
            "package/partials/favorites.html#favorite_btn",
            {"package": package},
        )
