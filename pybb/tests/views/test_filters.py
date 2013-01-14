# -*- coding: utf-8 -*-
from django.test import TransactionTestCase
from django.core.urlresolvers import reverse

from pybb.tests.base import SharedTestModule
from pybb.models import Post


class FiltersTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial(post=False)

    def test_filters(self):
        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        self.login_client()
        response = self.client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = u'test\n \n \n\nmultiple empty lines\n'
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.all()[0].body, u'test\nmultiple empty lines')
