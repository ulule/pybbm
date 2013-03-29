from haystack.utils import highlighting

from django.utils.html import mark_safe
import re

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
    def singularize_query(self):
        self.singulars = []
        for word in list(self.query_words):
            if len(word) > 1 and word.endswith('s'):
                singular = word[:-1]
                self.query_words.add(singular)
                self.singulars.append(singular)

    def highlight(self, text_block):
        self.text_block, tags = extract_tags(text_block)
        self.singularize_query()
        locations = self.find_highlightable_words()
        # clean location to give a chance to plurals word to be fully
        # highlighted
        for singular in self.singulars:
            plural = "%ss" % singular
            if singular in locations and plural in locations:
                for idx in locations[plural]:
                    if idx in locations[singular]:
                        locations[singular].remove(idx)
        hl_text = self.render_html(locations, 0, len(self.text_block))
        return mark_safe(hl_text % tuple(tags))




