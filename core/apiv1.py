from django.http import HttpResponseGone

apiv1_gone_msg = """APIv1 was removed on April 2, 2015.
Please switch to APIv3:

<ul>
    <li><a href="https://www.djangopackages.org/api/v3/">APIv3 Endpoint</a></li>
    <li><a href="http://djangopackagesorg.readthedocs.io/en/latest/apiv3_docs.html">APIv3 Documentation</a></li>
    <li><a href="http://www.pydanny.com/phasing-out-django-packages-apiv1-apiv2.html">APIv1 end-of-life notification</a></li>
</ul>

"""

def apiv1_gone(request):
    return HttpResponseGone(apiv1_gone_msg)
