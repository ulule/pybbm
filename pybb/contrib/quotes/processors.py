from pybb.processors import BaseProcessor
from pybb.contrib.quotes import settings


class QuotePreProcessor(BaseProcessor):
    def render(self):
        """strip all quotes deeper than PYBB_QUOTES_MAX_DEPTH"""
        max_depth = settings.PYBB_QUOTES_MAX_DEPTH
        if max_depth < 0:
            # nothing to do
            return self.body
        START_TAG = '[quote'
        END_TAG = '[/quote]'
        depth = 0
        body = u""
        cursor = 0
        while True:
            start = self.body.find(START_TAG, cursor)
            end = self.body.find(END_TAG, cursor)
            if start == end:
                body += self.body[cursor:]
                break
            if end < start or start == -1:
                next_cursor = end + len(END_TAG)
                if depth <= max_depth:
                    body += self.body[cursor:next_cursor]
                cursor = next_cursor
                depth -= 1
            elif start < end:
                if depth <= max_depth:
                    body += self.body[cursor:start]
                cursor = self.body.find(']', start) + 1
                depth += 1
                if depth <= max_depth:
                    body += self.body[start:cursor]
        return body
