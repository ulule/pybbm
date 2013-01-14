from __future__ import absolute_import

import bbcode

from pybb import defaults
from pybb.util import load_class
from pybb.engines.base import BaseMarkupEngine, BaseQuoteEngine


class BBCodeMarkupEngine(BaseMarkupEngine):
    simple_formatters = {
        'left': ('<div style="text-align:left;">%(value)s</div>', None),
        'center': ('<div style="text-align:center;">%(value)s</div>', None),
        'right': ('<div style="text-align:right;">%(value)s</div>', None),
        'ul': ('<ul>%(value)s</ul>', None),
        'ol': ('<ol>%(value)s</ol>', None),
        'li': ('<li>%(value)s</li>', None),
        'youtube': ('<iframe width="560" height="315" frameborder="0" src="http://www.youtube.com/embed/%(value)s?wmode=opaque" data-youtube-id="%(value)s" allowfullscreen=""></iframe>', None),
    }

    formatters = {
        'url': ('pybb.engines.bbcode.formatters.url', None),
        'img': ('pybb.engines.bbcode.formatters.img', {'render_embedded': False}),
        'spoiler': ('pybb.engines.bbcode.formatters.spoiler', None),
        'size': ('pybb.engines.bbcode.formatters.font_size', None),
        'font': ('pybb.engines.bbcode.formatters.font_family', None),
        'email': ('pybb.engines.bbcode.formatters.email', None),
    }

    def __init__(self, *args, **kwargs):
        super(BBCodeMarkupEngine, self).__init__(*args, **kwargs)

        self.parser = bbcode.Parser(replace_links=False, escape_html=False)

        simple_formatters = self.simple_formatters.items() + list(defaults.PYBB_BBCODE_MARKUP_SIMPLE_FORMATTERS)

        for tag_name, (format_str, context) in simple_formatters:
            if context:
                self.parser.add_simple_formatter(tag_name, format_str, **context)
            else:
                self.parser.add_simple_formatter(tag_name, format_str)

        formatters = self.formatters.items() + list(defaults.PYBB_BBCODE_MARKUP_FORMATTERS)

        for tag_name, (formatter_name, context) in formatters:
            if context:
                self.parser.add_formatter(tag_name, load_class(formatter_name), **context)
            else:
                self.parser.add_formatter(tag_name, load_class(formatter_name))

    def render(self, context=None):
        if not context:
            context = {}

        context['obj'] = self.obj

        return self.parser.format(self.message, **context)


class BBCodeQuoteEngine(BaseQuoteEngine):
    def render(self):
        return '[quote="%s;%d"]%s[/quote]\n' % (self.username,
                                                self.post.pk,
                                                self.post.body)
