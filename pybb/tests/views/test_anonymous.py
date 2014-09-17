from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from pybb import defaults
from pybb.compat import get_user_model
from pybb.tests.base import TestCase
from pybb.models import Post, Topic, Forum


class AnonymousTest(TestCase):
    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_ANONYMOUS_USERNAME = defaults.PYBB_ANONYMOUS_USERNAME
        defaults.PYBB_ENABLE_ANONYMOUS_POST = True
        defaults.PYBB_ANONYMOUS_USERNAME = 'Anonymous'
        self.user = get_user_model().objects.create_user('Anonymous', 'Anonymous@localhost', 'Anonymous')

        self.parent_forum = Forum.objects.create(name='foo')

        self.forum = Forum.objects.create(name='xfoo', description='bar', forum=self.parent_forum)
        self.topic = Topic.objects.create(name='etopic', forum=self.forum, user=self.user)
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'pybb', 'post')
        self.user.user_permissions.add(add_post_permission)

    def test_anonymous_posting(self):
        post_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        response = self.client.get(post_url)
        values = self.get_form_values(response)
        values['body'] = 'test anonymous'
        response = self.client.post(post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Post.objects.filter(body='test anonymous')), 1)
        self.assertEqual(Post.objects.get(body='test anonymous').user, self.user)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_ANONYMOUS_USERNAME = self.ORIG_PYBB_ANONYMOUS_USERNAME
