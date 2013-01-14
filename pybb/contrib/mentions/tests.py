from django.test import TransactionTestCase

from pybb.tests.base import SharedTestModule
from pybb.models.base import markup
from pybb.contrib.mentions.processors import MentionProcessor
from pybb.contrib.mentions.models import Mention

from pybb.models import Post


class MentionsTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial(post=False)

    def test_processors(self):
        self.post = Post(topic=self.topic, user=self.user, body='@thoas is right!')
        processor = MentionProcessor(self.post.body, obj=self.post)

        self.assertEqual(processor.render(), u'[mention=1]thoas[/mention] is right!')

        self.post.save()

        body = markup(self.post.body, obj=self.post)

        self.assertEqual(body, '@<a class="mention" href="/users/thoas/">thoas</a> is right!')

        self.assertEqual(Mention.objects.filter(post=self.post,
                                                from_user=self.post.user,
                                                to_user=self.staff).count(), 1)

    def test_multiple_mentions(self):
        multiple_mentions = Post(topic=self.topic, user=self.user, body='@thoas is right and @oleiade or @zeus!')

        processor = MentionProcessor(multiple_mentions.body, obj=multiple_mentions)

        self.assertEqual(processor.render(), u'[mention=1]thoas[/mention] is right and [mention=2]oleiade[/mention] or [mention=0]zeus[/mention]!')
        multiple_mentions.save()

        self.assertEqual(Mention.objects.filter(post=multiple_mentions).count(), 3)
