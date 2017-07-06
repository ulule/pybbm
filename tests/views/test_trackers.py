from django.core.urlresolvers import reverse
from django.test.client import Client

from pybb.models import ForumReadTracker, TopicReadTracker, Topic, Post, Forum
from pybb.compat import get_user_model

from tests.base import TestCase


class TrackersTest(TestCase):
    def test_read_tracking_multi_user(self):
        self.post

        topic_1 = self.topic
        topic_2 = Topic(name='topic_2', forum=self.forum, user=self.user)
        topic_2.save()

        Post(topic=topic_2, user=self.user, body='one').save()

        user_ann = get_user_model().objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        user_bob = get_user_model().objects.create_user('bob', 'bob@localhost', 'bob')
        client_bob = Client()
        client_bob.login(username='bob', password='bob')

        #  Two topics, each with one post. everything is unread, so the db should reflect that:
        self.assertEqual(TopicReadTracker.objects.all().count(), 0)
        self.assertEqual(ForumReadTracker.objects.all().count(), 0)

        #  user_ann reads topic_1, she should get one topic read tracker, there should be no forum read trackers
        client_ann.get(topic_1.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann, topic=topic_1).count(), 1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 0)

        #  user_bob reads topic_1, he should get one topic read tracker, there should be no forum read trackers
        client_bob.get(topic_1.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob, topic=topic_1).count(), 1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 0)

        #  user_bob reads topic_2, he should get a forum read tracker,
        #  there should be no topic read trackers for user_bob
        client_bob.get(topic_2.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=user_bob, forum=self.forum).count(), 1)

        #  user_ann creates topic_3, there should be a new topic read tracker in the db
        topic_create_url = reverse('pybb:topic_create', kwargs={'forum_id': self.forum.id})
        response = client_ann.get(topic_create_url)
        values = self.get_form_values(response)
        values['body'] = 'topic_3'
        values['name'] = 'topic_3'
        values['poll_type'] = 0
        response = client_ann.post(topic_create_url, data=values, follow=True)

        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)

        topic_3 = Topic.objects.order_by('-updated')[0]
        self.assertEqual(topic_3.name, 'topic_3')

        #  user_ann posts to topic_1, a topic they've already read, no new trackers should be created (existing one is updated)
        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': topic_1.id})
        response = client_ann.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test tracking'
        response = client_ann.post(post_create_url, values, follow=True)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)

        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        previous_time = ForumReadTracker.objects.all()[0].time_stamp

        # user bob reads topic 1 which he already read, topic tracker recreated, forum tracker untouched (topic 3 still unread)
        client_bob.get(topic_1.get_absolute_url())
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(TopicReadTracker.objects.all().count(), 3)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 1)

        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        previous_time = ForumReadTracker.objects.all()[0].time_stamp

        # user bob reads topic 3, topic tracker purged, forum tracker updated
        client_bob.get(topic_3.get_absolute_url())
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertGreater(ForumReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 0)

    def test_read_tracking_multi_forum(self):
        self.post

        topic_1 = self.topic
        topic_2 = Topic(name='topic_2', forum=self.forum, user=self.user)
        topic_2.save()

        Post(topic=topic_2, user=self.user, body='one').save()

        forum_2 = Forum(name='forum_2', description='bar', forum=self.parent_forum)
        forum_2.save()

        Topic(name='garbage', forum=forum_2, user=self.user).save()

        self.login_as(self.user)

        #  everything starts unread
        self.assertEqual(ForumReadTracker.objects.count(), 0)
        self.assertEqual(TopicReadTracker.objects.count(), 0)

        #  user reads topic_1, they should get one topic read tracker, there should be no forum read trackers
        self.client.get(topic_1.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=self.user).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=self.user, topic=topic_1).count(), 1)

        #  user reads topic_2, they should get a forum read tracker,
        #  there should be no topic read trackers for the user
        self.client.get(topic_2.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.count(), 0)
        self.assertEqual(ForumReadTracker.objects.count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.user, forum=self.forum).count(), 1)

    def test_forum_mark_as_read(self):
        url = reverse('pybb:forum_mark_as_read')

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertRedirects(response, reverse('pybb:index'))

        self.assertEqual(ForumReadTracker.objects.filter(user=self.staff).count(), Forum.objects.count())

    def test_forum_mark_as_read_specific(self):
        sub_forum = Forum.objects.create(name='sub_forum', forum=self.forum)
        sub_sub_forum = Forum.objects.create(name='sub_sub_forum', forum=sub_forum)

        url = reverse('pybb:forum_mark_as_read')

        self.login_as(self.staff)

        response = self.client.post(url, data={
            'forum_id': self.forum.pk
        })

        self.assertRedirects(response, self.forum.get_absolute_url())

        self.assertEqual(ForumReadTracker.objects.filter(user=self.staff, forum=self.forum).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.staff, forum=sub_forum).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.staff, forum=sub_sub_forum).count(), 1)

    def test_topic_tracker_redirect_view(self):
        self.login_as(self.staff)

        self.post

        response = self.client.get(reverse('pybb:topic_tracker_redirect', kwargs={
            'topic_id': self.topic.pk
        }))

        self.assertRedirects(response, self.topic.get_absolute_url(), status_code=301)

        TopicReadTracker.objects.create(topic=self.topic,
                                        user=self.staff)

        response = self.client.get(reverse('pybb:topic_tracker_redirect', kwargs={
            'topic_id': self.topic.pk
        }))

        self.client.get(self.topic.get_absolute_url())

        post = Post(topic=self.topic, user=self.user, body='test')
        post.save()

        response = self.client.get(reverse('pybb:topic_tracker_redirect', kwargs={
            'topic_id': self.topic.pk
        }))

        self.assertRedirects(response, post.get_absolute_url(), status_code=301)
