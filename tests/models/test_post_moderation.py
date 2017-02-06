from pybb.models import Post, Topic
from tests.base import TestCase


class ModelsModerationTest(TestCase):

    def test_post_moderation_topic_moderation_status_lifecycle(self):
        user = self.user
        topic = Topic.objects.create(name='topic name test', user=user, forum=self.forum)
        original_post = Post.objects.create(body='new post test', topic=topic, user=user, on_moderation=True)
        self.assertEqual(topic.on_moderation, Topic.MODERATION_IS_IN_MODERATION)

        original_post.on_moderation = False
        original_post.save()
        self.assertEqual(Topic.objects.get(pk=topic.id).on_moderation, Topic.MODERATION_IS_CLEAN)

        new_post = Post.objects.create(body='new post test2', topic=topic, user=user, on_moderation=True)
        self.assertEqual(Topic.objects.get(pk=topic.id).on_moderation, Topic.MODERATION_HAS_POSTS_IN_MODERATION)

        new_post.on_moderation = False
        new_post.save()
        self.assertEqual(Topic.objects.get(pk=topic.id).on_moderation, Topic.MODERATION_IS_CLEAN)

        new_post.deleted = True
        new_post.save()
        self.assertEqual(Topic.objects.get(pk=topic.id).on_moderation, Topic.MODERATION_IS_CLEAN)

        Post.objects.create(body='new post test3', topic=topic, user=user, on_moderation=True)
        self.assertEqual(Topic.objects.get(pk=topic.id).on_moderation, Topic.MODERATION_HAS_POSTS_IN_MODERATION)

        original_post.deleted = True
        original_post.save()
        self.assertEqual(Topic.objects.get(pk=topic.id).on_moderation, Topic.MODERATION_IS_IN_MODERATION)
