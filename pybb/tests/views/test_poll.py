# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

from pybb.tests.base import SharedTestModule
from pybb import defaults
from pybb.models import PollAnswer, Topic, Poll


class PollTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()
        self.PYBB_POLL_MAX_ANSWERS = defaults.PYBB_POLL_MAX_ANSWERS
        defaults.PYBB_POLL_MAX_ANSWERS = 2

    def test_poll_add(self):
        topic_create_url = reverse('pybb:topic_create', kwargs={'forum_id': self.forum.id})
        self.login_client()
        response = self.client.get(topic_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 0  # poll_type = None, create topic without poll answers
        values['poll_question'] = 'q1'
        values['answers-0-text'] = 'answer1'
        values['answers-1-text'] = 'answer2'
        values['answers-TOTAL_FORMS'] = 2
        response = self.client.post(topic_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name')

        self.assertIsNone(new_topic.poll)
        self.assertFalse(PollAnswer.objects.filter(poll=new_topic.poll).exists())  # no answers here

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['answers-0-text'] = 'answer1'  # not enough answers
        values['answers-TOTAL_FORMS'] = 1
        response = self.client.post(topic_create_url, values, follow=True)
        self.assertFalse(Topic.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['answers-0-text'] = 'answer1'  # too many answers
        values['answers-1-text'] = 'answer2'
        values['answers-2-text'] = 'answer3'
        values['answers-TOTAL_FORMS'] = 3
        response = self.client.post(topic_create_url, values, follow=True)
        self.assertFalse(Topic.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1  # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['answers-0-text'] = 'answer1'  # two answers - what do we need to create poll
        values['answers-1-text'] = 'answer2'
        values['answers-TOTAL_FORMS'] = 2
        response = self.client.post(topic_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

        new_topic = Topic.objects.get(name='test poll name 1')

        self.assertEqual(new_topic.poll.question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(poll=new_topic.poll).count(), 2)

    def test_poll_edit(self):
        edit_topic_url = reverse('pybb:post_update', kwargs={'pk': self.post.id})
        self.login_client()
        response = self.client.get(edit_topic_url)
        values = self.get_form_values(response)
        values['poll_type'] = 1  # add_poll
        values['poll_question'] = 'q1'
        values['answers-0-text'] = 'answer1'
        values['answers-1-text'] = 'answer2'
        values['answers-TOTAL_FORMS'] = 2
        response = self.client.post(edit_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

        topic = Topic.objects.get(id=self.topic.id)

        self.assertEqual(topic.poll.type, 1)
        self.assertEqual(topic.poll.question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(poll=topic.poll).count(), 2)

        values = self.get_form_values(self.client.get(edit_topic_url))
        values['poll_type'] = 2  # change_poll type
        values['poll_question'] = 'q100'  # change poll question
        values['answers-0-text'] = 'answer100'  # change poll answers
        values['answers-1-text'] = 'answer200'
        values['answers-TOTAL_FORMS'] = 2
        response = self.client.post(edit_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Topic.objects.get(id=self.topic.id).poll.type, 2)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll.question, 'q100')
        self.assertEqual(PollAnswer.objects.filter(poll=topic.poll).count(), 2)
        self.assertTrue(PollAnswer.objects.filter(text='answer100').exists())
        self.assertTrue(PollAnswer.objects.filter(text='answer200').exists())
        self.assertFalse(PollAnswer.objects.filter(text='answer1').exists())
        self.assertFalse(PollAnswer.objects.filter(text='answer2').exists())

        values['poll_type'] = 0  # remove poll
        values['answers-0-text'] = 'answer100'  # no matter how many answers we provide
        values['answers-TOTAL_FORMS'] = 1
        response = self.client.post(edit_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertIsNone(Topic.objects.get(id=self.topic.id).poll)

        self.assertEqual(PollAnswer.objects.filter(poll=topic.poll).count(), 0)

    def test_poll_voting(self):
        def recreate_poll(poll_type):

            if self.topic.poll:
                self.topic.poll.delete()

            poll = Poll(type=poll_type)
            poll.save()

            self.topic.poll = poll
            self.topic.save()

            PollAnswer.objects.create(poll=poll, text='answer1')
            PollAnswer.objects.create(poll=poll, text='answer2')

        self.login_client()
        recreate_poll(poll_type=Poll.TYPE_SINGLE)
        vote_url = reverse('pybb:topic_poll_vote', kwargs={'pk': self.topic.id})
        my_answer = PollAnswer.objects.all()[0]
        values = {'answers': my_answer.id}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_votes(), 1)
        self.assertEqual(PollAnswer.objects.get(id=my_answer.id).votes(), 1)
        self.assertEqual(PollAnswer.objects.get(id=my_answer.id).votes_percent(), 100.0)

         # already voted
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 400)  # bad request status

        recreate_poll(poll_type=Poll.TYPE_MULTIPLE)
        values = {'answers': [a.id for a in PollAnswer.objects.all()]}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [1, 1, ])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [50.0, 50.0, ])

    def tearDown(self):
        defaults.PYBB_POLL_MAX_ANSWERS = self.PYBB_POLL_MAX_ANSWERS
