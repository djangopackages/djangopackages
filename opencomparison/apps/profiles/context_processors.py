from django.conf import settings
from django.utils.functional import lazy, memoize, SimpleLazyObject

def lazy_profile(request):
    """
    Returns context variables required by templates that assume a profile
    on each request
    """

    def get_user_profile():
        if hasattr(request,'profile'):
            return request.profile
        else:
            return request.user.get_profile()

    data = {
        'profile': SimpleLazyObject(get_user_profile),
        'ACCOUNT_OPEN_SIGNUP': settings.ACCOUNT_OPEN_SIGNUP, # TODO - put this into the request some other, better way
        }
    return data
