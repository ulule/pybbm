# -*- coding: utf-8 -*-
from django.urls import reverse

from tests.base import TestCase
from pybb.models import Post


class FiltersTest(TestCase):
    def test_filters(self):
        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        self.login()
        response = self.client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = u'test\n \n \n\nmultiple empty lines\n'
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.all()[0].body, u'test\nmultiple empty lines')
