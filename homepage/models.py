import datetime

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from grid.models import Grid
from package.models import BaseModel, Package


class RotatorManager(models.Manager):

    def get_current(self):
        now = datetime.datetime.now()
        return self.get_queryset().filter(start_date__lte=now, end_date__gte=now)


class Dpotw(BaseModel):

    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))

    objects = RotatorManager()

    class Meta:
        ordering = ('-start_date', '-end_date',)
        get_latest_by = 'created'

        verbose_name = "Django Package of the Week"
        verbose_name_plural = "Django Packages of the Week"

    def __str__(self):
        return '%s : %s - %s' % (self.package.title, self.start_date, self.end_date)

    def get_absolute_url(self):
        return reverse("package", args=[self.package.slug])


class Gotw(BaseModel):

    grid = models.ForeignKey(Grid, on_delete=models.CASCADE)

    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))

    objects = RotatorManager()

    class Meta:
        ordering = ('-start_date', '-end_date',)
        get_latest_by = 'created'

        verbose_name = "Grid of the Week"
        verbose_name_plural = "Grids of the Week"

    def __str__(self):
        return '%s : %s - %s' % (self.grid.title, self.start_date, self.end_date)

    def get_absolute_url(self):
        return reverse("grid", args=[self.grid.slug])


class PSA(BaseModel):
    """ Public Service Announcement on the homepage """

    body_text = models.TextField(_("PSA Body Text"), blank=True, null=True)

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'

        verbose_name = "Public Service Announcement"
        verbose_name_plural = "Public Service Announcements"

    def __str__(self):
        return "{0} : {1}".format(self.created, self.body_text)
