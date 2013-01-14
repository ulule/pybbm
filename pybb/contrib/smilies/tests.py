from django.test import TransactionTestCase

from pybb.tests.base import SharedTestModule
from pybb.contrib.smilies.processors import SmileyProcessor

from pybb.models import Post


class SmiliesTest(TransactionTestCase, SharedTestModule):
    fixtures = ['smilies.json']

    def setUp(self):
        self.create_user()
        self.create_initial(post=False)

    def test_processors(self):
        self.post = Post(topic=self.topic, user=self.user, body='this is a smiiiile! :D')
        processor = SmileyProcessor(self.post.body, obj=self.post)

        self.assertEqual(processor.render(use_cache=False),
                         u'this is a smiiiile! [img class="smiley" alt=":D" title="lol"]pybb/smilies/lol.png[/img]')
