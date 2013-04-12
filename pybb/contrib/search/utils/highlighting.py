import re

from django.utils.html import mark_safe

from haystack.utils import highlighting

tag_re = re.compile(r'<[^>]*?>')


def extract_tags(html):
    """
    reutrn a string with all html tags replaced by '%s' placeholder and a list of
    stripped tags
    """
    tags = []
    html = html.replace('%', '%%')

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

    def find_highlightable_words(self):
        # Use a set so we only do this once per unique word.
        word_positions = {}

        # Pre-compute the length.
        end_offset = len(self.text_block)
        lower_text_block = self.text_block.lower()

        for word in self.query_words:
            if not word in word_positions:
                word_positions[word] = []

            start_offset = 0

            while start_offset < end_offset:
                next_offset = lower_text_block.find(word, start_offset, end_offset)

                # If we get a -1 out of find, it wasn't found. Bomb out and
                # start the next word.
                if next_offset == -1:
                    break

                # Fix a bug due to extract_tags() for words that start
                # with s: '%supper', if query is 'supper', becomes
                # '%<span>supper</span>'
                # wich in turn breaks string replacement
                if word.startswith('s'):
                    # count preceding '%' to quess if 's' is a formating mark
                    percents = 0
                    current_offset = next_offset - 1
                    while current_offset > -1:
                        if lower_text_block[current_offset] != '%':
                            break

                        percents += 1
                        current_offset += 1
                    if percents % 2:
                        # we got a '%s', forget this occurence
                        start_offset = next_offset + len(word)
                        continue

                word_positions[word].append(next_offset)
                start_offset = next_offset + len(word)

        return word_positions
