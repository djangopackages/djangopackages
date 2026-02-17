import waffle


SEARCH_PATH_PREFIXES = ("/search", "/search/")


class SearchVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO(searchv3): Remove this URLConf switching middleware once
        # searchv3 is stable and searchv2 is fully removed.
        if request.path_info.startswith(SEARCH_PATH_PREFIXES) and waffle.flag_is_active(
            request, "use_searchv3"
        ):
            request.urlconf = "searchv3.urlconf"
        return self.get_response(request)
