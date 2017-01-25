# -*- coding: utf-8 -*-
from django.core import mail
from django.core.urlresolvers import reverse

from tests.base import TestCase
from tests.filters import premoderate

from pybb.models import Post, Topic
from pybb import defaults

from mock import patch


class PreModerationTest(TestCase):
    def setUp(self):
        mail.outbox = []
        defaults.PYBB_PREMODERATION = 'tests.filters.premoderate'

    @patch('pybb.forms.base.pybb_premoderation', premoderate)
    def test_premoderation(self):
        self.login_as(self.user)

        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        response = self.client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation'
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation')
        self.assertEqual(post.on_moderation, True)

         # Post is visible by author
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        self.login_as(self.newbie)

        response = self.client.post(reverse('pybb:post_redirect'), data={
            'post_id': post.pk
        })

        self.assertEqual(response.status_code, 403)

        response = self.client.get(self.topic.get_absolute_url(), follow=True)
        self.assertNotContains(response, 'test premoderation')

        self.login_as(self.superuser)

        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        self.login_as(self.user)

        response = self.client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation staff'
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation staff')
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test premoderation staff')

        self.login_as(self.superuser)

        post = Post.objects.get(body='test premoderation')
        response = self.client.get(reverse('pybb:post_moderate', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 200)

         # Now all can see this post:
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

         # Other users can't moderate
        post.on_moderation = True
        post.save()

        self.login_as(self.newbie)

        response = self.client.get(reverse('pybb:post_moderate', kwargs={'pk': post.id}), follow=True)

        self.assertEqual(response.status_code, 403)

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

        self.login_as(self.newbie)

        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'new topic name')

        response = self.client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 404)

        self.login_as(self.superuser)

        response = self.client.get(reverse('pybb:post_moderate',
                                           kwargs={'pk': Post.objects.get(body='new topic test').id}),
                                   follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic name')
        response = self.client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        defaults.PYBB_PREMODERATION = False
