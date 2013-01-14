from django.test import TransactionTestCase
from django.contrib.auth.models import User

from pybb.tests.base import SharedTestModule
from pybb.models import Moderator, Post, Forum, Topic

from mock import patch

from guardian.models import UserObjectPermission


class ModelsTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()

        self.newbie = User.objects.create_user('newbie', 'newbie@localhost', 'newbie')

    def test_post_is_accessible_by_authenticated_users(self):
        self.assertTrue(self.post.is_accessible_by(self.user))
        self.assertTrue(self.post.is_accessible_by(self.staff))
        self.assertTrue(self.post.is_accessible_by(self.superuser))

    def test_post_in_forum_hidden_is_accessible_by_unauthenticated_user(self):
        self.forum.hidden = True
        self.forum.save()

        with patch.object(User, 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = False

            self.assertFalse(self.post.is_accessible_by(self.newbie))

        self.assertTrue(self.post.is_accessible_by(self.user))
        self.assertTrue(self.post.is_accessible_by(self.staff))
        self.assertTrue(self.post.is_accessible_by(self.superuser))

    def test_post_in_category_hidden_is_accessible_by_unauthenticated_user(self):
        self.parent_forum.hidden = True
        self.parent_forum.save()

        with patch.object(User, 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = False

            self.assertFalse(self.post.is_accessible_by(self.newbie))

        with patch.object(User, 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = True

            self.assertTrue(self.post.is_accessible_by(self.user))
            self.assertTrue(self.post.is_accessible_by(self.staff))
            self.assertTrue(self.post.is_accessible_by(self.superuser))

    def test_post_editable_by_users(self):
        self.assertTrue(self.post.is_editable_by(self.user))
        self.assertTrue(self.post.is_editable_by(self.staff))
        self.assertTrue(self.post.is_editable_by(self.superuser))
        self.assertFalse(self.post.is_editable_by(self.newbie))

    def test_post_editable_by_moderator_with_permission(self):
        self.assertFalse(self.post.is_editable_by(self.newbie))

        Moderator.objects.create(forum=self.post.topic.forum, user=self.newbie)

        self.assertFalse(self.post.is_editable_by(self.newbie, 'can_change_post'))

        UserObjectPermission.objects.assign('can_change_post', user=self.newbie, obj=self.post.topic.forum)

        self.post = Post.objects.get(pk=self.post.pk)

        with patch.object(User, 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = True

            self.assertTrue(self.post.is_editable_by(self.newbie))

    def test_is_posted_by(self):
        self.assertTrue(self.post.is_posted_by(self.user))
        self.assertFalse(self.post.is_posted_by(self.newbie))

    def test_topic_on_moderation(self):
        self.topic.on_moderation = True
        self.topic.save()

        with patch.object(User, 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = True

            self.assertTrue(self.post.is_accessible_by(self.user))
            self.assertTrue(self.post.is_accessible_by(self.staff))
            self.assertTrue(self.post.is_accessible_by(self.superuser))

            self.assertFalse(self.post.is_accessible_by(self.newbie))

            Moderator.objects.create(forum=self.post.topic.forum, user=self.newbie)

            self.assertTrue(self.post.is_accessible_by(self.newbie))

    def test_compute(self):
        # initials
        self.assertEqual(self.parent_forum.forum_count, 1)
        self.assertEqual(self.forum.forum_count, 0)

        parent_forum = Forum.objects.get(pk=self.parent_forum.pk)

        self.assertEqual(parent_forum.topic_count, 1)
        self.assertEqual(parent_forum.post_count, 1)
        self.assertEqual(self.forum.topic_count, 1)
        self.assertEqual(self.forum.post_count, 1)

        forum = Forum.objects.create(name='bar', description='bar', forum=self.forum)

        topic = Topic(name='bar', forum=forum, user=self.user)
        topic.save()

        post = Post(topic=topic, user=self.user, body='my new post')
        post.save()

        self.assertEqual(topic.post_count, 1)
        self.assertEqual(forum.topic_count, 1)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 2)

        new_topic = Topic(name='foo', forum=self.forum, user=self.user)
        new_topic.save()

        new_post = Post(topic=topic, user=self.user, body='my new post')
        new_post.save()

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 3)

        post.mark_as_deleted(commit=True)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 2)

        self.assertTrue(Topic.objects.get(pk=topic.pk).deleted)

        self.assertEqual(Forum.objects.get(pk=forum.pk).topic_count, 0)
        self.assertEqual(Forum.objects.get(pk=forum.pk).post_count, 0)

        new_topic.mark_as_deleted()

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 1)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 1)
