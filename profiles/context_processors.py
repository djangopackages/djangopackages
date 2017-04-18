from django.utils.functional import SimpleLazyObject


def lazy_profile(request):
    """
    Returns context variables required by templates that assume a profile
    on each request
    """

    def get_user_profile():
        if hasattr(request, 'profile'):
            return request.profile
        else:
            return request.user.profile

    data = {
        'profile': SimpleLazyObject(get_user_profile),
        }
    return data
