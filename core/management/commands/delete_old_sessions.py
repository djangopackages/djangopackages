from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session

"""
>>> def clean(count):
...   for idx, s in enumerate(Session.objects.filter(expire_date__lt=now)[:count+1]):
...     s.delete()
...     if str(idx).endswith('000'): print idx
...   print "{0} records left".format(Session.objects.filter(expire_date__lt=now).count())
... 
"""

class Command(NoArgsCommand):

    args = '<count count ...>'
    help = "Delete old sessions"

    def handle(self, *args, **options):
        old_sessions = Session.objects.filter(expire_date__lt=datetime.now())

        self.stdout.write("Deleting {0} expired sessions".format(
                old_sessions.count()
            )
        )

        for index, session in enumerate(old_sessions):
            session.delete()
            if str(idx).endswith('000'):
                self.stdout.write("{0} records deleted".format(index)

        self.stdout.write("{0} expired sessions remaining".format(
                Session.objects.filter(expire_date__lt=datetime.now())
            )
        )
