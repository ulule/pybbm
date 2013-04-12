from django.test import TransactionTestCase

from pybb.tests.base import SharedTestModule

from pybb.contrib.search.utils.highlighting import Highlighter, extract_tags


class SearchHighlighterTest(TransactionTestCase, SharedTestModule):
    def highlight(self, query, text):
        h = Highlighter(query)
        return h.highlight(text)

    def test_simple_highlighting(self):
        text = 'ligne 1<br/>ligne 2 coucou <a href="#">lien</a>'
        query = u'coucou'
        expected = 'ligne 1<br/>ligne 2 <span class="highlighted">coucou</span> <a href="#">lien</a>'
        self.assertEqual(self.highlight(query, text), expected)

    def test_plural_highlighting(self):
        text = 'ligne 1<br/>ligne 2 coucou <a href="#">lien</a>'
        query = u'coucous'
        expected = 'ligne 1<br/>ligne 2 <span class="highlighted">coucou</span> <a href="#">lien</a>'
        self.assertEqual(self.highlight(query, text), expected)

    def test_s_word_highlighting(self):
        # <br/> is fist replaced by '%s'. this may lead to formating errors if
        # the query starts with 's'
        text = 'ligne 1 <br/>upper ligne 2 coucou <a href="#">lien</a>'
        self.assertEqual(extract_tags(text), ('ligne 1 %supper ligne 2 coucou %slien%s', ['<br/>', '<a href="#">', '</a>']))
        query = u'supper'
        self.assertEqual(self.highlight(query, text), text)
        # combined with textual '%'
        text = 'ligne 1 %<br/>upper ligne 2 coucou <a href="#">lien</a>'
        self.assertEqual(extract_tags(text), ('ligne 1 %%%supper ligne 2 coucou %slien%s', ['<br/>', '<a href="#">', '</a>']))
        self.assertEqual(self.highlight(query, text), text)
