import os
import requests

from pybb.models import Moderator, Post, Forum, Topic
from tests.base import TestCase
from pybb.compat import get_user_model

from mock import patch

from guardian.models import UserObjectPermission


class ModelsTest(TestCase):
    def test_post_is_accessible_by_authenticated_users(self):
        self.assertTrue(self.post.is_accessible_by(self.user))
        self.assertTrue(self.post.is_accessible_by(self.staff))
        self.assertTrue(self.post.is_accessible_by(self.superuser))

    def test_sync_cover(self):
        images = [
            'http://dummy.host/image.png'
        ]

        body = """<div>My message %s</div>""" % ''.join(['<img src="%s" />' % image for image in images])

        self.post.body = body
        self.post.body_html = body
        self.post.save()

        self.topic.first_post = self.post

        for index, image in enumerate(self.post.images):
            self.assertEqual(image, images[index])

        with patch.object(requests, 'get') as get_method:
            file = os.path.join(os.path.dirname(__file__), '..', 'static', 'pybb', 'img', 'attachment.png')

            content = open(file, 'rb').read()

            get_method.return_value = type('response', (object, ), {'content': content, 'status_code': 200})

            self.post.topic.sync_cover()

            self.assertTrue(self.post.topic.cover)

    def test_post_in_forum_hidden_is_accessible_by_unauthenticated_user(self):
        self.forum.hidden = True
        self.forum.save()

        with patch.object(get_user_model(), 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = False

            self.assertFalse(self.post.is_accessible_by(self.newbie))

        self.assertTrue(self.post.is_accessible_by(self.user))
        self.assertTrue(self.post.is_accessible_by(self.staff))
        self.assertTrue(self.post.is_accessible_by(self.superuser))

    def test_post_in_category_hidden_is_accessible_by_unauthenticated_user(self):
        self.parent_forum.hidden = True
        self.parent_forum.save()

        with patch.object(get_user_model(), 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = False

            self.assertFalse(self.post.is_accessible_by(self.newbie))

        with patch.object(get_user_model(), 'is_authenticated') as is_authenticated:
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

        UserObjectPermission.objects.assign_perm('can_change_post', self.newbie, obj=self.post.topic.forum)

        self.post = Post.objects.get(pk=self.post.pk)

        with patch.object(get_user_model(), 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = True

            self.assertTrue(self.post.is_editable_by(self.newbie))

    def test_is_posted_by(self):
        self.assertTrue(self.post.is_posted_by(self.user))
        self.assertFalse(self.post.is_posted_by(self.newbie))

    def test_topic_on_moderation(self):
        self.post

        self.topic.on_moderation = True
        self.topic.save()

        with patch.object(get_user_model(), 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = True

            self.assertTrue(self.post.is_accessible_by(self.user))
            self.assertTrue(self.post.is_accessible_by(self.staff))
            self.assertTrue(self.post.is_accessible_by(self.superuser))

            self.assertFalse(self.post.is_accessible_by(self.newbie))

            Moderator.objects.create(forum=self.post.topic.forum, user=self.newbie)

            self.assertTrue(self.post.is_accessible_by(self.newbie))

    def test_compute(self):
        # initials
        self.assertEqual(self.forum.forum_count, 0)
        self.assertEqual(self.parent_forum.forum_count, 1)

        self.topic
        self.post

        parent_forum = Forum.objects.get(pk=self.parent_forum.pk)

        self.assertEqual(parent_forum.topic_count, 1)
        self.assertEqual(parent_forum.post_count, 1)
        self.assertEqual(self.forum.topic_count, 1)
        self.assertEqual(self.forum.post_count, 1)

        # Add (forum --> topic --> post) in self.forum
        forum = Forum.objects.create(name='bar', description='bar', forum=self.forum)

        topic = Topic(name='bar', forum=forum, user=self.user)
        topic.save()

        post = Post(topic=topic, user=self.user, body='my new post')
        post.save()

        self.assertEquals(Topic.objects.get(pk=topic.pk).get_first_post(), post)
        self.assertEqual(topic.post_count, 1)
        self.assertEqual(forum.topic_count, 1)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).post_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).post_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 2)

        # Add (topic --> post) in self.forum
        new_topic = Topic(name='foo', forum=self.forum, user=self.user)
        new_topic.save()

        new_post = Post(topic=new_topic, user=self.user, body='my new post')
        new_post.save()
        self.assertEquals(Topic.objects.get(pk=new_topic.pk).get_first_post(), new_post)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).post_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).post_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 3)

        # delete post in (self.parent_forum --> self.forum --> forum --> topic)
        post.mark_as_deleted(commit=True)

        self.assertTrue(Topic.objects.get(pk=topic.pk).deleted)
        self.assertEquals(Topic.objects.get(pk=topic.pk).get_first_post(), post)
        self.assertTrue(Topic.objects.get(pk=topic.pk).get_first_post().deleted)

        self.assertEqual(Forum.objects.get(pk=forum.pk).topic_count, 0)
        self.assertEqual(Forum.objects.get(pk=forum.pk).post_count, 0)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 2)

        # delete new_topic in (self.parent_forum --> self.forum)
        new_topic.mark_as_deleted()

        self.assertTrue(Topic.objects.get(pk=new_topic.pk).deleted)
        self.assertEquals(Topic.objects.get(pk=new_topic.pk).get_first_post(), new_post)
        self.assertTrue(Topic.objects.get(pk=new_topic.pk).get_first_post().deleted)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 1)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 1)

        # undelete new_topic in (self.parent_forum --> self.forum)
        new_topic.mark_as_undeleted()

        self.assertFalse(Topic.objects.get(pk=new_topic.pk).deleted)
        self.assertEquals(Topic.objects.get(pk=new_topic.pk).get_first_post(), new_post)
        self.assertFalse(Topic.objects.get(pk=new_topic.pk).get_first_post().deleted)

        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 2)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 2)

        # undelete post in (self.parent_forum --> self.forum --> forum --> topic)
        post.mark_as_undeleted(commit=True)

        self.assertFalse(Topic.objects.get(pk=topic.pk).deleted)
        self.assertEquals(Topic.objects.get(pk=topic.pk).get_first_post(), post)
        self.assertFalse(Topic.objects.get(pk=topic.pk).get_first_post().deleted)

        self.assertEqual(Forum.objects.get(pk=forum.pk).post_count, 1)
        self.assertEqual(Forum.objects.get(pk=forum.pk).topic_count, 1)
        self.assertEqual(Forum.objects.get(pk=self.forum.pk).post_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.forum.pk).topic_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).post_count, 3)
        self.assertEqual(Forum.objects.get(pk=self.parent_forum.pk).topic_count, 3)

    def test_move_forum(self):
        # Initial state
        topic = self.topic
        forum = self.topic.forum
        original_parent = self.topic.forum.forum

        original_parent.refresh_from_db(fields=('forum_ids', 'forum'))
        forum.refresh_from_db(fields=('forum_ids', 'forum'))
        topic.refresh_from_db(fields=('forum_ids', 'forum'))

        assert original_parent.forum_id is None
        assert original_parent.forum_ids == []

        assert forum.forum_id == original_parent.id
        assert forum.forum_ids == [original_parent.id]

        assert topic.forum_id == forum.id
        assert topic.forum_ids == [forum.id, original_parent.id]

        # move forum to new_parent
        new_parent = Forum.objects.create(name='zfoo', description='bar', forum=self.parent_forum)

        forum.forum = new_parent
        forum.save(update_fields=('forum',))

        original_parent.refresh_from_db(fields=('forum_ids', 'forum'))
        new_parent.refresh_from_db(fields=('forum_ids', 'forum'))
        forum.refresh_from_db(fields=('forum_ids', 'forum'))
        topic.refresh_from_db(fields=('forum_ids', 'forum'))

        assert original_parent.forum_id is None
        assert original_parent.forum_ids == []

        assert new_parent.forum_id == original_parent.id
        assert new_parent.forum_ids == [original_parent.id]

        assert forum.forum_id == new_parent.id
        assert forum.forum_ids == [new_parent.id, original_parent.id]

        assert topic.forum_id == forum.id
        assert topic.forum_ids == [forum.id, new_parent.id, original_parent.id]
