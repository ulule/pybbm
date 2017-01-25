from django.core.urlresolvers import reverse

from tests.base import TestCase


class UsersTest(TestCase):
    def test_user_posts_view(self):
        url = reverse('pybb:user_posts', kwargs={
            'username': self.user.username
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response,
                                'pybb/user/post_list.html')

    def test_user_posts_delete_view(self):
        self.login_as(self.staff)

        url = reverse('pybb:user_posts_delete', kwargs={
            'username': self.user.username
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response,
                                'pybb/user/posts_delete.html')

    def test_user_posts_delete_complete(self):
        self.login_as(self.staff)

        url = reverse('pybb:user_posts_delete', kwargs={
            'username': self.user.username
        })

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.user.posts.filter(deleted=False).count(), 0)

        self.assertRedirects(response, reverse('pybb:user_posts', kwargs={
            'username': self.user.username
        }))
