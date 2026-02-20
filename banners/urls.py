from django.urls import path

from banners.views import DismissBannerView

app_name = "banners"

urlpatterns = [
    path("dismiss/<int:banner_id>/", DismissBannerView.as_view(), name="dismiss"),
]
