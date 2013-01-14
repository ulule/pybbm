from django.test import TransactionTestCase
from django.core.urlresolvers import reverse

from pybb.tests.base import SharedTestModule


class UsersTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()

    def test_user_posts_view(self):
        url = reverse('pybb:user_posts', kwargs={
            'username': self.user.username
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.login_client(username='thoas', password='$ecret')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response,
                                'pybb/user/post_list.html')

    def test_user_posts_delete_view(self):
        self.login_client(username='thoas', password='$ecret')

        url = reverse('pybb:user_posts_delete', kwargs={
            'username': self.user.username
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response,
                                'pybb/user/posts_delete.html')

    def test_user_posts_delete_complete(self):
        self.login_client(username='thoas', password='$ecret')

        url = reverse('pybb:user_posts_delete', kwargs={
            'username': self.user.username
        })

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.user.posts.filter(deleted=False).count(), 0)

        self.assertRedirects(response, reverse('pybb:user_posts', kwargs={
            'username': self.user.username
        }))
