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
    packages = Column(accessor="gridpackage_count", verbose_name="Packages")
    features = Column(empty_values=(), orderable=False, verbose_name="Features")

    class Meta:
        fields = ["title", "description", "last_modified", "packages", "features"]
        model = Grid
        template_name = "django_tables2/bootstrap.html"

    def render_description(self, value, record):
        return format_html(emojize(record.description))

    def render_features(self, value, record):
        return record.feature_set.count()

    def render_title(self, value, record):
        return format_html(
            '<a href="{}">{}</a>'.format(
                reverse("grid", kwargs={"slug": record.slug}), emojize(record.title)
            )
        )
