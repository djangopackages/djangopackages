from django.urls import path

from favorites.views import FavoritePackage


urlpatterns = [
    path("add/<int:id>/", FavoritePackage.as_view(), name="add_favorite"),
]
