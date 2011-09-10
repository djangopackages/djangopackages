from sys import stdout
from time import sleep, gmtime, strftime

from django.core.management.base import CommandError, NoArgsCommand
from django.template.loader import get_template
from django.template import Context, Template

from package.models import Category, Package, PackageExample, Commit

DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S +0000"

class Command(NoArgsCommand):
    
    help = "Export all the data"
    
    def handle(self, *args, **options):
        
        print >> stdout, "Commencing export now at %s " % strftime(DATETIME_FORMAT, gmtime())
        
        output = ""
        
        # Let's do categories
        category_tmpl = get_template('core/export/package.category.py')
        data = dict(categories = Category.objects.all())
        c = Context(data)
        output += category_tmpl.render(c)
        
        package_tmpl = get_template('core/export/package.package.py')
        data = dict(packages = Package.objects.all())
        c = Context(data)
        output += package_tmpl.render(c)
        
        print >> stdout, "Finished at %s" % strftime(DATETIME_FORMAT, gmtime())
        print output