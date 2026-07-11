import emoji
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html

from core.utils import PackageStatus


register = template.Library()


class ParticipantURLNode(template.Node):
    def __init__(self, repo, participant):
        self.repo = template.Variable(repo)
        self.participant = template.Variable(participant)

    def render(self, context):
        repo = self.repo.resolve(context)
        participant = self.participant.resolve(context)
        if repo_user_url := repo.user_url:
            user_url = repo_user_url % participant
        else:
            user_url = f"{repo.url}/{participant}"
        return user_url


@register.tag
def participant_url(parser, token):
    try:
        tag_name, repo, participant = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two arguments" % token.contents.split()[0]
        )
    return ParticipantURLNode(repo, participant)


@register.filter()
@stringfilter
def emojify(value):
    return emoji.emojize(value)


@register.filter
def is_in(value, arg):
    """Check if a value is in a list/tuple."""
    if arg is None:
        return False
    return value in arg


@register.filter(name="package_dev_status_badge", is_safe=True)
def package_dev_status_badge(status, muted=False):
    """Render a styled HTML badge for a PyPI development status.

    `status` should be an integer matching PackageStatus values.

    Optional filter argument can be used to force a muted style, e.g.
    {{ version.development_status|package_dev_status_badge:version.hidden }}
    """

    try:
        status_value = int(status) if status is not None else int(PackageStatus.UNKNOWN)
    except (TypeError, ValueError):
        status_value = int(PackageStatus.UNKNOWN)

    try:
        choice = PackageStatus(status_value)
    except ValueError:
        choice = PackageStatus.UNKNOWN

    pretty = choice.pretty_label

    base = (
        "inline-flex items-center py-1 px-2 text-xs font-medium rounded border "
        "whitespace-nowrap"
    )

    if muted:
        return format_html(
            '<span class="{} bg-muted text-muted-foreground border-border">{}</span>',
            base,
            pretty,
        )

    styles = {
        PackageStatus.UNKNOWN: (
            "bg-muted text-muted-foreground border-border",
            "ph-question",
        ),
        PackageStatus.PLANNING: (
            "bg-sky-50 text-sky-700 border-sky-200 "
            "dark:bg-sky-500/10 dark:text-sky-300 dark:border-sky-500/25",
            "ph-compass",
        ),
        PackageStatus.PRE_ALPHA: (
            "bg-orange-50 text-orange-800 border-orange-200 "
            "dark:bg-orange-500/10 dark:text-orange-300 dark:border-orange-500/25",
            "ph-flask",
        ),
        PackageStatus.ALPHA: (
            "bg-yellow-50 text-yellow-800 border-yellow-200 "
            "dark:bg-yellow-500/10 dark:text-yellow-300 dark:border-yellow-500/25",
            "ph-flask",
        ),
        PackageStatus.BETA: (
            "bg-indigo-50 text-indigo-700 border-indigo-200 "
            "dark:bg-indigo-500/10 dark:text-indigo-300 dark:border-indigo-500/25",
            "ph-test-tube",
        ),
        PackageStatus.STABLE: (
            "bg-green-50 text-green-700 border-green-200 "
            "dark:bg-green-500/10 dark:text-green-300 dark:border-green-500/25",
            "ph-check-circle",
        ),
        PackageStatus.MATURE: (
            "bg-emerald-50 text-emerald-700 border-emerald-200 "
            "dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/25",
            "ph-seal-check",
        ),
        PackageStatus.INACTIVE: (
            "bg-rose-50 text-rose-700 border-rose-200 "
            "dark:bg-rose-500/10 dark:text-rose-300 dark:border-rose-500/25",
            "ph-archive",
        ),
    }

    css, icon = styles.get(choice, styles[PackageStatus.UNKNOWN])

    return format_html(
        '<span class="{} {}"><i class="mr-1 text-xs ph-bold {}"></i>{}</span>',
        base,
        css,
        icon,
        pretty,
    )
