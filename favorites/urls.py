from django.urls import path

from favorites.views import FavoritePackage, UnFavoritePackage


urlpatterns = [
    path("add/<int:id>/", FavoritePackage.as_view(), name="add_favorite"),
    path("remove/<int:id>/", UnFavoritePackage.as_view(), name="remove_favorite"),
]
