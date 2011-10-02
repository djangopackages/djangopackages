from django.conf import settings

def core_values(request):
    """
    A nice pun. But this is how we stick handy data everywhere.
    """
    
    data = {
        'SITE_TITLE': getattr(settings, "SITE_TITLE", "Django Packages"),
        'FRAMEWORK_TITLE': getattr(settings, "SITE_TITLE", "Django")        
        }
    return data
