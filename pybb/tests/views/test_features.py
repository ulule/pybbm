# -*- coding: utf-8 -*-
import time
from datetime import timedelta, date

from django.test import TransactionTestCase
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User

from pybb import defaults
from pybb.models import (Post, Topic, Forum, TopicRedirection, Subscription, PostDeletion)

from pybb.tests.base import html, SharedTestModule

from mock import patch


class FeaturesTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = False
        defaults.PYBB_ENABLE_ANONYMOUS_POST = False
        self.create_user()
        self.create_initial()
        mail.outbox = []

    def test_base(self):
         # Check index page
        url = reverse('pybb:index')
        response = self.client.get(url)
        parser = html.HTMLParser(encoding='utf8')
        tree = html.fromstring(response.content, parser=parser)
        self.assertContains(response, u'foo')
        self.assertContains(response, self.forum.get_absolute_url())
        self.assertTrue(defaults.PYBB_DEFAULT_TITLE in tree.xpath('//title')[0].text_content())
        self.assertEqual(len(response.context['forums']), 1)

    def test_forum_page(self):
         # Check forum page
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['forum'], self.forum)
        tree = html.fromstring(response.content)
        self.assertTrue(tree.xpath('//a[@href="%s"]' % self.topic.get_absolute_url()))
        self.assertTrue(tree.xpath('//title[contains(text(),"%s")]' % self.forum.name))
        self.assertFalse(tree.xpath('//a[contains(@href,"?page=")]'))
        self.assertFalse(response.context['is_paginated'])

    def test_profile_edit(self):
         # Self profile edit
        self.login_client()
        response = self.client.get(reverse('profile_update'))
        self.assertEqual(response.status_code, 200)
        values = self.get_form_values(response, 'profile-edit')
        values['signature'] = 'test signature'
        response = self.client.post(reverse('profile_update'), data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test signature')
         # Test empty signature
        values['signature'] = ''
        response = self.client.post(reverse('profile_update'), data=values, follow=True)
        self.assertEqual(len(response.context['form'].errors), 0)

    def test_pagination_and_topic_addition(self):
        for i in range(0, defaults.PYBB_FORUM_PAGE_SIZE + 3):
            topic = Topic(name='topic_%s_' % i, forum=self.forum, user=self.user)
            topic.save()
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(len(response.context['topic_list']), defaults.PYBB_FORUM_PAGE_SIZE)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['paginator'].num_pages,
                         ((defaults.PYBB_FORUM_PAGE_SIZE + 3) / defaults.PYBB_FORUM_PAGE_SIZE) + 1)

    def test_bbcode_and_topic_title(self):
        response = self.client.get(self.topic.get_absolute_url())
        tree = html.fromstring(response.content)
        self.assertTrue(self.topic.name in tree.xpath('//title')[0].text_content())
        self.assertContains(response, self.post.body_html)
        self.assertContains(response, u'bbcode <strong>test</strong>')

    def test_topic_addition(self):
        self.login_client()
        topic_create_url = reverse('pybb:topic_create', kwargs={'forum_id': self.forum.id})
        response = self.client.get(topic_create_url)
        values = self.get_form_values(response)
        values['body'] = 'new topic test'
        values['name'] = 'new topic name'
        values['poll_type'] = 0
        response = self.client.post(topic_create_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Topic.objects.filter(name='new topic name').exists())

    def test_post_deletion(self):
        post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        post.delete()
        Topic.objects.get(id=self.topic.id)
        Forum.objects.get(id=self.forum.id)

    def test_topic_deletion(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()
        post = Post(topic=topic, user=self.user, body='two')
        post.save()
        post.delete()
        Topic.objects.get(id=topic.id)
        Forum.objects.get(id=self.forum.id)
        topic.delete()
        Forum.objects.get(id=self.forum.id)

    def test_topic_move_view(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()

        topic_move_url = reverse('pybb:topic_move')

        self.login_client(username='thoas', password='$ecret')

        response = self.client.post(topic_move_url, data={
            'topic_ids': [topic.pk]
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['form'].forms), 1)
        self.assertTemplateUsed(response, 'pybb/topic/move.html')

    def test_topic_move_complete(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()

        topic_merge_url = reverse('pybb:topic_move')

        self.login_client(username='thoas', password='$ecret')

        name = 'new name for a topic'

        response = self.client.post(topic_merge_url, data={
            'topic_ids': [topic.pk],
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-name': name,
            'form-0-forum': self.forum.pk,
            'form-0-redirection_type': TopicRedirection.TYPE_PERMANENT_REDIRECT,
            'submit': 1
        })

        self.assertRedirects(response, reverse('pybb:index'))

        topic = Topic.objects.get(pk=topic.pk)

        self.assertTrue(topic.redirect)
        self.failUnless(topic.redirection is not None)

        redirection = topic.redirection

        new_topic = redirection.to_topic

        self.assertEqual(new_topic.name, name)
        self.assertEqual(new_topic.post_count, 1)

    def test_topic_merge_view(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()

        topic_merge_url = reverse('pybb:topic_merge')

        self.login_client(username='thoas', password='$ecret')

        response = self.client.post(topic_merge_url, data={
            'topic_ids': [topic.pk]
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['form'].forms), 1)
        self.assertTemplateUsed(response, 'pybb/topic/merge.html')

    def test_posts_move_view(self):
        post_move_url = reverse('pybb:post_move')

        self.login_client(username='thoas', password='$ecret')

        response = self.client.post(post_move_url, data={
            'post_ids': [self.post.pk]
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pybb/post/move.html')

    def test_posts_move_complete_new_topic(self):
        post_move_url = reverse('pybb:post_move')

        self.login_client(username='thoas', password='$ecret')

        post_ids = [self.post.pk]

        response = self.client.post(post_move_url, data={
            'post_ids': post_ids,
            'choice': '0',
            'name': 'new topic name',
            'forum': self.forum.pk,
            'submit': '1'
        })

        self.assertEqual(response.status_code, 302)

        for post_id in post_ids:
            post = Post.objects.get(pk=post_id)

            self.assertEqual(post.topic.name, 'new topic name')
            self.assertEqual(post.topic.forum, self.forum)

    def test_posts_move_complete_existing_topic(self):
        forum = Forum.objects.create(name='temporary forum')

        topic = Topic.objects.create(name='move_topic', forum=forum, user=self.superuser)

        post_move_url = reverse('pybb:post_move')

        self.login_client(username='thoas', password='$ecret')

        post_ids = [self.post.pk]

        response = self.client.post(post_move_url, data={
            'post_ids': post_ids,
            'choice': '1',
            'topic': topic.pk,
            'submit': '1'
        })

        self.assertEqual(response.status_code, 302)

        for post_id in post_ids:
            post = Post.objects.get(pk=post_id)
            self.assertEqual(post.topic, topic)

    def test_topic_merge_complete(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()

        topic_merge_url = reverse('pybb:topic_merge')

        self.login_client(username='thoas', password='$ecret')

        response = self.client.post(topic_merge_url, data={
            'topic_ids': [topic.pk],
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-topic': self.topic.pk,
            'submit': 1
        })

        self.assertRedirects(response, reverse('pybb:index'))

    def test_forum_updated(self):
        time.sleep(1)
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()
        post = Post.objects.get(id=post.id)
        self.assertTrue(self.forum.updated == post.created)

    def test_hidden(self):
        client = Client()
        parent = Forum(name='hcat', hidden=True)
        parent.save()

        forum_in_hidden = Forum(name='in_hidden', forum=parent)
        forum_in_hidden.save()

        topic_in_hidden = Topic(forum=forum_in_hidden, name='in_hidden', user=self.user)
        topic_in_hidden.save()

        forum_hidden = Forum(name='hidden', forum=self.parent_forum, hidden=True)
        forum_hidden.save()

        topic_hidden = Topic(forum=forum_hidden, name='hidden', user=self.user)
        topic_hidden.save()

        post_hidden = Post(topic=topic_hidden, user=self.user, body='hidden')
        post_hidden.save()

        post_in_hidden = Post(topic=topic_in_hidden, user=self.user, body='hidden')
        post_in_hidden.save()

        self.assertFalse(parent.id in [c.id for c in client.get(reverse('pybb:index')).context['forums']])
        self.assertEqual(client.get(parent.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 302)

        self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed_topics')), topic_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed_topics')), topic_in_hidden.get_absolute_url())

        self.assertNotContains(client.get(reverse('pybb:feed_posts')), post_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed_posts')), post_in_hidden.get_absolute_url())
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 302)

        client.login(username='zeus', password='zeus')

        self.assertTrue(parent.id in [c.id for c in client.get(reverse('pybb:index')).context['forums']])

        self.assertContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())

        self.assertEqual(client.get(parent.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 200)
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(parent.id in [c.id for c in client.get(reverse('pybb:index')).context['forums']])
        self.assertContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())

        self.assertEqual(client.get(parent.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 200)

    def test_staff(self):
        client = Client()
        parent = Forum(name='hcat', staff=True)
        parent.save()

        forum_in_staff = Forum(name='in_staff', forum=parent)
        forum_in_staff.save()

        topic_in_staff = Topic(forum=forum_in_staff, name='in_staff', user=self.user)
        topic_in_staff.save()

        forum_staff = Forum(name='staff', forum=self.parent_forum, staff=True)
        forum_staff.save()

        topic_staff = Topic(forum=forum_staff, name='staff', user=self.user)
        topic_staff.save()

        post_staff = Post(topic=topic_staff, user=self.user, body='staff')
        post_staff.save()

        post_in_staff = Post(topic=topic_in_staff, user=self.user, body='staff')
        post_in_staff.save()

        self.assertFalse(parent.id in [c.id for c in client.get(reverse('pybb:index')).context['forums']])
        self.assertEqual(client.get(parent.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(forum_in_staff.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_in_staff.get_absolute_url()).status_code, 404)

        self.assertEqual(client.get(forum_staff.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_staff.get_absolute_url()).status_code, 404)

        client.login(username='zeus', password='zeus')

        self.assertFalse(parent.id in [c.id for c in client.get(reverse('pybb:index')).context['forums']])

        self.assertNotContains(client.get(reverse('pybb:index')), forum_staff.get_absolute_url())

        self.assertEqual(client.get(parent.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(forum_in_staff.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_in_staff.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(forum_staff.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_staff.get_absolute_url()).status_code, 404)

        self.user.is_staff = True
        self.user.save()

        self.assertTrue(parent.id in [c.id for c in client.get(reverse('pybb:index')).context['forums']])

        self.assertEqual(client.get(parent.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_in_staff.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_in_staff.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_staff.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_staff.get_absolute_url()).status_code, 200)

    def test_inactive(self):
        self.login_client()
        url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        response = self.client.get(url)
        values = self.get_form_values(response)
        values['body'] = 'test ban'
        response = self.client.post(url, values, follow=True)

        self.assertEqual(len(Post.objects.filter(body='test ban')), 1)
        self.user.is_active = False
        self.user.save()
        values['body'] = 'test ban 2'
        self.client.post(url, values, follow=True)
        self.assertEqual(len(Post.objects.filter(body='test ban 2')), 0)

    def get_csrf(self, form):
        return form.xpath('//input[@name="csrfmiddlewaretoken"]/@value')[0]

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username='zeus', password='zeus')
        post_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        response = client.get(post_url)
        values = self.get_form_values(response)
        del values['csrfmiddlewaretoken']
        response = client.post(post_url, values, follow=True)
        self.assertNotEqual(response.status_code, 200)
        response = client.get(self.topic.get_absolute_url())
        values = self.get_form_values(response)
        response = client.post(reverse('pybb:post_create', kwargs={'topic_id': self.topic.id}), values, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_ajax_preview(self):
        self.login_client()
        response = self.client.post(reverse('pybb:post_preview'), data={'data': '[b]test bbcode ajax preview[/b]'})
        self.assertEqual(response.status_code, 200)

    def test_headline(self):
        self.forum.headline = 'test <b>headline</b>'
        self.forum.save()
        client = Client()
        self.assertContains(client.get(self.forum.get_absolute_url()), 'test <b>headline</b>')

    def test_quote(self):
        self.login_client()
        response = self.client.get(reverse('pybb:post_create', kwargs={'topic_id': self.topic.id}), data={'quote_id': self.post.id, 'body': 'test tracking'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.body)

    def test_post_update(self):
        self.login_client()

        post_update_url = reverse('pybb:post_update', kwargs={'pk': self.post.id})
        response = self.client.get(post_update_url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'

        with patch.object(Post, 'is_updatable') as is_updatable:
            is_updatable.return_value = True

            response = self.client.post(post_update_url, data=values, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Post.objects.get(pk=self.post.id).body, 'test edit')
        response = self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test edit')

        post = Post.objects.get(pk=self.post.pk)

        self.assertFalse(post.updated is None)

        updated = post.updated

         # Check admin form
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(post_update_url)
        self.assertEqual(response.status_code, 200)

        self.login_client(username='thoas', password='$ecret')

        response = self.client.post(post_update_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)

        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(updated, post.updated)

    def test_admin_post_add(self):
        self.user.is_staff = True
        self.user.save()
        self.login_client()
        response = self.client.post(reverse('pybb:post_create',
                                            kwargs={'topic_id': self.topic.id}),
                                    data={
                                        'quote_id': self.post.id,
                                        'body': 'test admin post',
                                        'user': 'zeus'
                                    }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test admin post')

    def test_stick(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        self.assertEqual(self.client.get(reverse('pybb:topic_stick', kwargs={'pk': self.topic.id}), follow=True).status_code, 200)
        self.assertEqual(self.client.get(reverse('pybb:topic_unstick', kwargs={'pk': self.topic.id}), follow=True).status_code, 200)

    def test_delete_post_view_superuser(self):
        post = Post(topic=self.topic, user=self.user, body='test to delete')
        post.save()
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.post(reverse('pybb:post_delete', args=[post.id]), follow=True)
        self.assertEqual(response.status_code, 200)
         # Check that topic and forum exists ;)
        self.assertEqual(Topic.objects.filter(id=self.topic.id).count(), 1)
        self.assertEqual(Forum.objects.filter(id=self.forum.id).count(), 1)

         # Delete topic
        response = self.client.post(reverse('pybb:post_delete', args=[self.post.id]), follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Post.objects.filter(id=self.post.id,
                                             deleted=False).count(), 0)
        self.assertEqual(Topic.objects.filter(id=self.topic.id,
                                              deleted=False).count(), 0)
        self.assertEqual(Forum.objects.filter(id=self.forum.id).count(), 1)

    def test_delete_post_view_own_user(self):
        post = Post(topic=self.topic, user=self.user, body='test to delete')
        post.save()

        self.login_client()

        response = self.client.post(reverse('pybb:post_delete', args=[post.id]))
        self.assertEqual(response.status_code, 302)

        self.assertRaises(Post.DoesNotExist, lambda: Post.objects.get(pk=post.pk, deleted=False))

        self.assertNotEqual(post.deletion, None)

    def test_undelete_post_view_own_user(self):
        post = Post(topic=self.topic, user=self.user, body='test to delete', deleted=True)
        post.save()

        PostDeletion.objects.create(post=post, user=self.user)

        self.login_client()

        response = self.client.post(reverse('pybb:post_delete', args=[post.id]))
        self.assertEqual(response.status_code, 302)

        post = Post.objects.get(pk=post.pk)

        self.assertRaises(PostDeletion.DoesNotExist, lambda: post.deletion)

        self.assertFalse(post.deleted)

    def test_delete_post_topic_view(self):
        self.login_client()

        response = self.client.post(reverse('pybb:post_delete', args=[self.post.id]))

        self.assertEqual(response.status_code, 302)

        post = Post.objects.get(pk=self.post.pk)

        self.assertTrue(post.deleted)

        self.assertNotEqual(self.post.deletion, None)

    def test_undelete_post_topic_view(self):
        post = Post(topic=self.topic, user=self.user, body='test to delete', deleted=True)
        post.save()
        post.mark_as_deleted(user=self.user)

        self.login_client()

        self.post.mark_as_deleted(user=self.user)

        response = self.client.post(reverse('pybb:post_delete', args=[self.post.id]))

        self.assertEqual(response.status_code, 302)

        self.post = Post.objects.get(pk=self.post.pk)

        self.assertRaises(PostDeletion.DoesNotExist, lambda: self.post.deletion)

        self.assertFalse(self.post.deleted)

        self.assertTrue(Post.objects.get(pk=post.pk).deleted)

    def test_open_close(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        post_create_url = reverse('pybb:post_create', args=[self.topic.id])
        response = self.client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test closed'
        response = self.client.get(reverse('pybb:topic_close', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('pybb:topic_open', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_delete_topic_view(self):
        self.login_client(username='thoas', password='$ecret')
        response = self.client.get(reverse('pybb:topic_delete', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/topic/delete.html')

    def test_delete_topic_complete(self):
        self.login_client(username='thoas', password='$ecret')
        response = self.client.post(reverse('pybb:topic_delete', args=[self.topic.id]), follow=True)
        self.assertRedirects(response, self.topic.forum.get_absolute_url())

        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertTrue(topic.deleted)

    def test_subscription(self):
        user = User.objects.create_user(username='user2', password='user2', email='user2@example.com')
        client = Client()
        client.login(username='user2', password='user2')
        response = client.post(reverse('pybb:subscription_create'), data={
            'topic_id': self.topic.pk,
            'type': Subscription.TYPE_INSTANT_ALERT
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.topic.get_absolute_url())
        self.assertTrue(user in list(self.topic.subscribers.all()))
        new_post = Post(topic=self.topic, user=self.user, body='test subscribtion юникод')
        new_post.save()
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])
        response = client.post(reverse('pybb:subscription_delete'), data={
            'topic_id': self.topic.pk
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.topic.get_absolute_url())
        self.assertTrue(user not in list(self.topic.subscribers.all()))

    def test_subscription_change(self):
        subscription = Subscription.objects.create(topic=self.topic,
                                                   type=Subscription.TYPE_INSTANT_ALERT,
                                                   user=self.staff)

        self.login_client(username='thoas', password='$ecret')

        response = self.client.post(reverse('pybb:subscription_change'), data={
            'topic_ids': [self.topic.pk],
            'type': Subscription.TYPE_DAILY_ALERT
        })

        self.assertRedirects(response, reverse('pybb:subscription_list'))

        subscription = Subscription.objects.get(pk=subscription.pk)

        self.assertEqual(subscription.type, Subscription.TYPE_DAILY_ALERT)

    def test_subscription_list_view(self):
        Subscription.objects.create(topic=self.topic,
                                    type=Subscription.TYPE_INSTANT_ALERT,
                                    user=self.staff)

        self.login_client(username='thoas', password='$ecret')

        response = self.client.get(reverse('pybb:subscription_list'))

        self.assertTemplateUsed(response, 'pybb/user/subscription_list.html')

        self.assertEqual(response.status_code, 200)

    def test_topic_redirect(self):
        response = self.client.get(self.topic.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        topic = Topic(name='to-etopic', forum=self.forum, user=self.user)
        topic.save()

        self.topic.redirect = True
        self.topic.save()

        redirection = TopicRedirection.objects.create(from_topic=self.topic, to_topic=topic)

        response = self.client.get(self.topic.get_absolute_url())

        self.assertRedirects(response, topic.get_absolute_url(), status_code=301)

        redirection.type = TopicRedirection.TYPE_NO_REDIRECT
        redirection.save()

        response = self.client.get(self.topic.get_absolute_url())

        self.assertEqual(response.status_code, 404)

        redirection.type = TopicRedirection.TYPE_EXPIRING_REDIRECT
        redirection.expired = date.today() + timedelta(days=1)
        redirection.save()

        response = self.client.get(self.topic.get_absolute_url())

        self.assertRedirects(response, topic.get_absolute_url())

        redirection.expired = date.today() - timedelta(days=1)
        redirection.save()

        response = self.client.get(self.topic.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_topic_updated(self):
        topic = Topic(name='etopic', forum=self.forum, user=self.user)
        topic.save()
        time.sleep(1)
        post = Post(topic=topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], topic)
        time.sleep(1)
        post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], self.topic)

    def test_topic_latest(self):
        url = reverse('pybb:topics_latest')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.login_client(username='thoas', password='$ecret')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'pybb/topic/latest.html')

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION
