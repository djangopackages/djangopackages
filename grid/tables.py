from django.urls import reverse
from django.utils.html import format_html
from django_tables2 import Column, Table, TemplateColumn
from emoji import emojize

from grid.models import Grid


class GridTable(Table):
    title = Column(orderable=False, verbose_name="Grid")
    description = Column(
        accessor="description", orderable=False, verbose_name="Description"
    )
    last_modified = TemplateColumn(
        "{{ record.modified|date }}", orderable=False, verbose_name="Last Modified"
    )
    packages = Column(
        accessor="gridpackage_count", orderable=False, verbose_name="Packages"
    )
    features = Column(empty_values=(), orderable=False, verbose_name="Features")

    def render_features(self, value, record):
        return record.feature_set.count()

    def render_title(self, value, record):
        return format_html(
            '<a href="{0}">{1}</a>'.format(
                reverse("grid", kwargs={"slug": record.slug}), emojize(record.title)
            )
        )

    class Meta:
        fields = ["title", "description", "last_modified", "packages", "features"]
        model = Grid
        template_name = "django_tables2/bootstrap.html"
