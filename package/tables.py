from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.html import format_html
from django_tables2 import Column, Table, TemplateColumn
from emoji import emojize

from package.models import Package


class PackageTable(Table):
    title = Column(empty_values=(), verbose_name="Title")
    commits = TemplateColumn(
        '<img class="package-githubcommits" src="https://chart.googleapis.com/chart?cht=bvg&chs=105x20&chd=t:{{record.commits_over_52}}&chco=666666&chbh=1,1,1&chds=0,20" />',
        orderable=False,
        verbose_name="Commits",
    )
    version = Column(accessor="pypi_version", orderable=False, verbose_name="Version")
    repo_watchers = Column(
        accessor="repo_watchers",
        verbose_name=format_html(
            "Stars <span class='glyphicon glyphicon-star'></span>"
        ),
    )
    repo_forks = Column(
        accessor="repo_forks",
        verbose_name=format_html(
            "Forks <span class='glyphicon glyphicon-random'></span>"
        ),
    )

    class Meta:
        fields = ["title", "commits", "version", "repo_watchers", "repo_forks"]
        model = Package
        template_name = "django_tables2/bootstrap.html"

    def render_repo_forks(self, value, record):
        return intcomma(record.repo_forks)

    def render_title(self, value, record):
        return format_html(
            '<a href="{}">{}</a>'.format(
                reverse("package", kwargs={"slug": record.slug}), emojize(record.title)
            )
        )

    def render_repo_watchers(self, value, record):
        return intcomma(record.repo_watchers)


class PackageByCategoryTable(PackageTable):
    # <td class="usage-container usage-holder">
    #     {% usage_button %}
    #     &nbsp;
    #     <span class="usage-count">{{ package.usage_count }}</span>
    # </td>
    # <td>{{ package.last_released.pretty_status }}</td>
    # "# Using This"
    usage_count = TemplateColumn(
        '<span class="usage-count">{{ record.usage_count }}</span>',
        # orderable=False,
        verbose_name="# Using This",
    )
    last_released = Column(
        empty_values=(), orderable=False, verbose_name="Development Status"
    )

    class Meta(PackageTable.Meta):
        fields = [
            "title",
            "commits",
            "version",
            "usage_count",
            "last_released",
            "repo_watchers",
            "repo_forks",
        ]

    def render_last_released(self, value, record):
        last_released = record.last_released()
        if last_released:
            return last_released.pretty_status
        return "Unknown"
