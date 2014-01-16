from pybb.tests.base import TestCase

from .processors import SmileyProcessor

from pybb.models import Post


class SmiliesTest(TestCase):
    fixtures = ['smilies.json']

    def test_processors(self):
        self.post = Post(topic=self.topic, user=self.user, body='this is a smiiiile! :D')
        processor = SmileyProcessor(self.post.body, obj=self.post)

        self.assertEqual(processor.render(use_cache=False),
                         u'this is a smiiiile! [img class="smiley" alt=":D" title="lol"]pybb/smilies/lol.png[/img]')
