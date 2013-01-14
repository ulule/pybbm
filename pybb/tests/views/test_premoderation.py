# -*- coding: utf-8 -*-
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.test.client import Client

from pybb.tests.base import SharedTestModule, premoderate
from pybb import defaults
from pybb.models import Post, Topic


class PreModerationTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = premoderate
        self.create_user()
        self.create_initial()
        mail.outbox = []

    def test_premoderation(self):
        self.client.login(username='zeus', password='zeus')
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

         # Post is not visible by others
        client = Client()
        response = client.post(reverse('pybb:post_redirect'), follow=True, data={
            'post_id': post.pk
        })
        self.assertEqual(response.status_code, 403)

        response = client.get(self.topic.get_absolute_url(), follow=True)
        self.assertNotContains(response, 'test premoderation')

         # But visible by superuser (with permissions)
        user = User.objects.create_user('admin', 'zeus@localhost', 'admin')
        user.is_superuser = True
        user.save()
        client.login(username='admin', password='admin')
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

         # user with names stats with allowed can post without premoderation
        user = User.objects.create_user('allowed_zeus', 'zeus@localhost', 'allowed_zeus')
        client.login(username='allowed_zeus', password='allowed_zeus')
        response = client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation staff'
        response = client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation staff')
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test premoderation staff')

         # Superuser can moderate
        user.is_superuser = True
        user.save()
        admin_client = Client()
        admin_client.login(username='admin', password='admin')
        post = Post.objects.get(body='test premoderation')
        response = admin_client.get(reverse('pybb:post_moderate', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 200)

         # Now all can see this post:
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

         # Other users can't moderate
        post.on_moderation = True
        post.save()
        client.login(username='zeus', password='zeus')
        response = client.get(reverse('pybb:post_moderate', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 403)

         # If user create new topic it goes to moderation if MODERATION_ENABLE
         # When first post is moderated, topic becomes moderated too
        self.client.login(username='zeus', password='zeus')
        topic_create_url = reverse('pybb:topic_create', kwargs={'forum_id': self.forum.id})
        response = self.client.get(topic_create_url)
        values = self.get_form_values(response)
        values['body'] = 'new topic test'
        values['name'] = 'new topic name'
        values['poll_type'] = 0
        response = self.client.post(topic_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic test')

        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'new topic name')
        response = client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 404)
        response = admin_client.get(reverse('pybb:post_moderate',
                                            kwargs={'pk': Post.objects.get(body='new topic test').id}),
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic name')
        response = client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION
