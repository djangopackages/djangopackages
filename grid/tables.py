from django.urls import reverse
from django.utils.html import format_html
from django_tables2 import Column, Table, TemplateColumn
from emoji import emojize

from grid.models import Grid


class GridTable(Table):
    title = Column(accessor="title", verbose_name="Grid")
    description = Column(
        accessor="description", orderable=False, verbose_name="Description"
    )
    last_modified = TemplateColumn(
        "{{ record.modified|date }}", accessor="modified", verbose_name="Last Modified"
    )
    total_packages = Column(accessor="gridpackage_count", verbose_name="Total Packages")
    active_packages = Column(
        accessor="active_gridpackage_count", verbose_name="Active Packages"
    )
    features = Column(
        accessor="feature_count", orderable=False, verbose_name="Features"
    )

    class Meta:
        fields = [
            "title",
            "description",
            "last_modified",
            "active_packages",
            "total_packages",
            "features",
        ]
        model = Grid
        template_name = "django_tables2/bootstrap.html"

    def render_description(self, value, record):
        return format_html("{}", emojize(record.description))

    def render_title(self, value, record):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("grid", kwargs={"slug": record.slug}),
            emojize(record.title),
        )
