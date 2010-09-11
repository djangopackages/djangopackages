import class_based_views

from package.models import Package


class PackageList(class_based_views.ListView):
    
    queryset             = Package.objects.select_related()