# -*- coding: utf-8 -*-
from django.core import mail
from django.core.urlresolvers import reverse
from pybb.models.base import BaseTopic

from tests.base import TestCase
from tests.filters import premoderate

from pybb.models import Post, Topic
from pybb import defaults

from exam import fixture

from mock import patch


class PreModerationTestPostModeration(TestCase):
    def setUp(self):
        mail.outbox = []

        self.login_as(self.user)

        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        response = self.client.get(post_create_url)

        values = self.get_form_values(response)
        values['body'] = 'test clean post'
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

        post = Post.objects.get(body='test clean post')
        self.assertEqual(post.on_moderation, False)
        self.assertEqual(post.topic.on_moderation, BaseTopic.MODERATION_IS_CLEAN)

        defaults.PYBB_PREMODERATION = 'tests.filters.premoderate'

    @fixture
    def pre_moderation_post(self):
        self.login_as(self.user)

        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        response = self.client.get(post_create_url)

        values = self.get_form_values(response)
        values['body'] = 'test premoderation'
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

        post = Post.objects.get(body='test premoderation')
        self.assertEqual(post.on_moderation, True)
        self.assertEqual(post.topic.on_moderation, BaseTopic.MODERATION_HAS_POSTS_IN_MODERATION)
        return post

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_post_is_visible_by_author(self):
        response = self.client.get(self.pre_moderation_post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_post_is_forbidden_for_other_regular_users(self):
        post = self.pre_moderation_post

        self.login_as(self.newbie)

        # direct access with url
        response = self.client.post(reverse('pybb:post_redirect'), data={
            'post_id': post.pk
        })
        self.assertEqual(response.status_code, 403)

        # access through topic
        response = self.client.get(self.topic.get_absolute_url(), follow=True)
        self.assertNotContains(response, 'test premoderation')

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_post_is_visible_for_superusers(self):
        post = self.pre_moderation_post

        self.login_as(self.superuser)
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_post_is_visible_after_moderation(self):
        post = self.pre_moderation_post

        self.login_as(self.superuser)
        response = self.client.get(reverse('pybb:post_moderate', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 200)

        self.login_as(self.newbie)
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_post_cant_be_moderated_by_anyone(self):
        post = self.pre_moderation_post

        self.login_as(self.newbie)
        response = self.client.get(reverse('pybb:post_moderate', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 403)

    def tearDown(self):
        defaults.PYBB_PREMODERATION = False


class PreModerationTestTopicModeration(TestCase):
    def setUp(self):
        mail.outbox = []
        defaults.PYBB_PREMODERATION = 'tests.filters.premoderate'

    def moderate_post(self, user,  post):
        self.login_as(user)
        response = self.client.get(reverse('pybb:post_moderate',
                                           kwargs={'pk': post.id}),
                                   follow=True)
        return response

    @fixture
    def pre_moderation_topic(self):
        self.login_as(self.user)

        topic_create_url = reverse('pybb:topic_create', kwargs={'forum_id': self.forum.id})
        response = self.client.get(topic_create_url)
        values = self.get_form_values(response)
        values['body'] = 'new topic test'
        values['name'] = 'new topic name'
        values['poll_type'] = 0
        response = self.client.post(topic_create_url, values, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic test')

        topic = Topic.objects.get(name='new topic name')
        self.assertEqual(topic.on_moderation, BaseTopic.MODERATION_IS_IN_MODERATION)
        return topic

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_topic_is_visible_by_author(self):
        topic = self.pre_moderation_topic

        self.login_as(self.user)
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic name')

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_topic_is_forbidden_for_other_regular_users(self):
        topic = self.pre_moderation_topic

        self.login_as(self.newbie)

        # access through forum
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'new topic name')

        # direct access with url
        response = self.client.get(topic.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_topic_is_visible_for_superusers(self):
        topic = self.pre_moderation_topic

        self.login_as(self.superuser)
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic name')

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_topic_is_visible_after_moderation(self):
        topic = self.pre_moderation_topic

        response = self.moderate_post(self.superuser, Post.objects.get(body='new topic test'))
        self.assertEqual(response.status_code, 200)

        self.login_as(self.newbie)
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic name')

        response = self.client.get(topic.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation_topic_cant_be_moderated_by_anyone(self):
        topic = self.pre_moderation_topic

        response = self.moderate_post(self.newbie, Post.objects.get(body='new topic test'))
        self.assertEqual(response.status_code, 403)

    def tearDown(self):
        defaults.PYBB_PREMODERATION = False
