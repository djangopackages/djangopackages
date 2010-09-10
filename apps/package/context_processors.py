def used_packages(request):
    context = {}
    # TODO: Cache this result...
    if request.user.is_authenticated():
        context['used_packages_list'] = request.user.package_set.values_list("pk", flat=True)
    return context