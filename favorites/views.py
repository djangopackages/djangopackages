from django.views.generic import View
from django.http import HttpResponse
from django.shortcuts import redirect
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
            return redirect("/")

        _, created = Favorite.objects.get_or_create(
            package=package, favorited_by=request.user
        )
        return HttpResponse(
            '<span class="glyphicon glyphicon-heart "></span> Favorited'
        )
