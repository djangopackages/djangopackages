from django.urls import path

from probes.views import ProbeSectionView, ProbeStatsView

app_name = "probes"

urlpatterns = [
    path("", ProbeStatsView.as_view(), name="stats"),
    path("<slug:section>/", ProbeSectionView.as_view(), name="section"),
]
