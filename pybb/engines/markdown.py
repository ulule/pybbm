from __future__ import absolute_import
from markdown import Markdown

from pybb.engines.base import BaseMarkupEngine, BaseQuoteEngine


class MarkdownMarkupEngine(BaseMarkupEngine):
    engine = Markdown
    params = {
        'safe_mode': 'escape'
    }

    def render(self):
        return self.engine(**self.params).convert(str)


class MarkdownQuoteEengine(BaseQuoteEngine):
    def render(self):
        return '>' + self.post.body.replace('\n', '\n>').replace('\r', '\n>') + '\n'
