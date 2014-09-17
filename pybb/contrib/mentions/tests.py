from pybb.tests.base import TestCase
from pybb.models.base import markup

from .processors import MentionProcessor
from .models import Mention

from pybb.models import Post


class MentionsTest(TestCase):
    def test_processors(self):
        self.user
        self.staff

        self.post = Post(topic=self.topic, user=self.user, body='@thoas is right!')
        processor = MentionProcessor(self.post.body, obj=self.post)

        self.assertEqual(processor.render(), u'[mention=%d]thoas[/mention] is right!' % self.staff.pk)

        self.post.save()

        body = markup(self.post.body, obj=self.post)

        self.assertEqual(body, '@<a class="mention" href="/users/thoas/">thoas</a> is right!')

        self.assertEqual(Mention.objects.filter(post=self.post,
                                                from_user=self.post.user,
                                                to_user=self.staff).count(), 1)

    def test_multiple_mentions(self):
        self.user
        self.staff
        self.superuser

        multiple_mentions = Post(topic=self.topic, user=self.user, body='@thoas is right and @oleiade or @zeus!')

        processor = MentionProcessor(multiple_mentions.body, obj=multiple_mentions)

        self.assertEqual(processor.render(), u'[mention=%d]thoas[/mention] is right and [mention=%d]oleiade[/mention] or [mention=%d]zeus[/mention]!' % (
            self.staff.pk,
            self.superuser.pk,
            self.user.pk
        ))
        multiple_mentions.save()

        self.assertEqual(Mention.objects.filter(post=multiple_mentions).count(), 3)
