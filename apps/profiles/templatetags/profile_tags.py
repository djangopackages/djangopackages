from django import template

register = template.Library()

@register.filter
def package_usage(user):
    return user.package_set.all()

@register.simple_tag
def user_display(user):
	""" TODO - turn this into an inclusion tag """
	return user