from django import template
from django.utils import simplejson

from pybb.contrib.smilies.models import Smiley
from pybb.contrib.smilies import settings


register = template.Library()


@register.inclusion_tag('_pybb_smiley_short_list.html')
def smiley_short_list():
    smilies = Smiley.objects.one_click()

    has_more = Smiley.objects.has_more()

    return {
        'smilies': smilies,
        'has_more': has_more,
        'style_class': settings.PYBB_SMILIES_STYLE_CLASS
    }


@register.inclusion_tag('_pybb_smiley_full_list.html')
def smiley_full_list():
    smilies = Smiley.objects.active()

    return {
        'smilies': smilies,
        'style_class': settings.PYBB_SMILIES_STYLE_CLASS
    }

@register.simple_tag
def smiley_json_list():
    dropdown = {}
    more = {}
    for smiley in Smiley.objects.active():
        if smiley.in_one_click:
            dropdown[smiley.pattern] = smiley.image.url
        else:
            more[smiley.pattern] = smiley.image.url
    return simplejson.dumps({
        'dropdown': dropdown,
        'more': more
    })
