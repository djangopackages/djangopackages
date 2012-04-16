from django import template

register = template.Library()


@register.filter
def package_usage(user):
    return user.package_set.all()
