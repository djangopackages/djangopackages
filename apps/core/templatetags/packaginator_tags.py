# -*- coding: utf-8 -*-
from classytags.helpers import InclusionTag
from django import template
from django.conf import settings


register = template.Library()


class FixedGA(InclusionTag):
    template = 'templatetags/ga.html'
    
    name = 'fixed_ga'
    
    def render_tag(self, context):
        URCHIN_ID = getattr(settings, "URCHIN_ID", None)
        if URCHIN_ID and not settings.DEBUG:
            return super(FixedGA, self).render_tag(context)
        return ''
    
    def get_context(self, context):
        """
        If it get's here, we already checked that this setting is set!
        """
        return {'URCHIN_ID': settings.URCHIN_ID}

register.tag(FixedGA)