import re

from django.utils.lru_cache import lru_cache

from pybb.processors import BaseProcessor

from . import settings
from .models import Smiley


def _get_smilies_re():
    escaped_patterns = []
    replacements = {}
    for smiley in Smiley.objects.for_matching():
        escaped_patterns.append(re.escape(smiley.pattern))
        replacements[smiley.pattern] = [smiley.image.url, smiley.pattern, smiley.title]

    return re.compile('|'.join(escaped_patterns)), replacements


@lru_cache()
def get_smilies_re():
    return _get_smilies_re()


class SmileyProcessor(BaseProcessor):
    def render(self, use_cache=True):
        smilies_re, replacements = get_smilies_re() if use_cache and settings.PYBB_SMILIES_USE_CACHE else get_smilies_re()

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
