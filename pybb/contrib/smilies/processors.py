import re

from django.utils.functional import memoize

from pybb.processors import BaseProcessor

from . import settings
from .models import Smiley

_cache = {}


def _get_smilies_re():
    escaped_patterns = []
    replacements = {}
    for smiley in Smiley.objects.for_matching():
        escaped_patterns.append(re.escape(smiley.pattern))
        replacements[smiley.pattern] = [smiley.image.url, smiley.pattern, smiley.title]

    return re.compile('|'.join(escaped_patterns)), replacements

get_smilies_re = memoize(_get_smilies_re, _cache, 0)


class SmileyProcessor(BaseProcessor):
    def render(self, use_cache=True):
        smilies_re, replacements = get_smilies_re() if use_cache and settings.PYBB_SMILIES_USE_CACHE else _get_smilies_re()

        def replace_func(matched):
            res = '[img class="%s" alt="%s" title="%s"]%s[/img]' % \
                (settings.PYBB_SMILIES_STYLE_CLASS,
                 replacements[matched.group(0)][1],
                 replacements[matched.group(0)][2],
                 replacements[matched.group(0)][0])
            return res

        body = self.body

        if replacements.values():
            body = smilies_re.sub(replace_func, body)

        return body
