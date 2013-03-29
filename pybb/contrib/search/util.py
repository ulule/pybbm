import re

from haystack.utils import highlighting

from django.utils.html import mark_safe

tag_re = re.compile(r'<[^>]*?>')


def extract_tags(html):
    """
    reutrn a string with all html tags replaced by '%s' placeholder and a list of
    stripped tags
    """
    tags = []

    def repl(m):
        tags.append(m.group(0))
        return '%s'

    text, nr = tag_re.subn(repl, html)
    return text, tags


class Highlighter(highlighting.Highlighter):
    """
    override haysatck defaul highlighter to keep html tags in the result
    """
    def highlight(self, text_block):
        self.text_block, tags = extract_tags(text_block)
        locations = self.find_highlightable_words()
        hl_text = self.render_html(locations, 0, len(self.text_block))
        return mark_safe(hl_text % tuple(tags))
