from django.core.cache import cache


def used_packages_list(request):
    context = {}
    if request.user.is_authenticated:
        cache_key = "sitewide_used_packages_list_%s" % request.user.pk
        used_packages_list = cache.get(cache_key)
        if used_packages_list is None:
            used_packages_list = request.user.package_set.values_list("pk", flat=True)
            cache.set(cache_key, used_packages_list, 60 * 60 * 24)
        context['used_packages_list'] = used_packages_list
    if 'used_packages_list' not in context:
        context['used_packages_list'] = []
    return context
