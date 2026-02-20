from django.http import HttpResponse
from django.views import View


class DismissBannerView(View):
    """Mark a banner as dismissed in the user's session."""

    http_method_names = ["post"]

    def post(self, request, banner_id):
        request.session[f"dismissed_banner_{banner_id}"] = True
        return HttpResponse("")
