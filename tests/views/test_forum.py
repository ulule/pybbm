from django.core.urlresolvers import reverse

from tests.base import TestCase
from pybb.forms import ForumForm, ModerationForm
from pybb.models import Forum, Moderator
from pybb import defaults


class ForumsTest(TestCase):
    def test_create_view(self):
        url = reverse('pybb:forum_create', kwargs={
            'forum_id': self.parent_forum.pk
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/forum/create.html')

        self.failUnless(isinstance(response.context['form'],
                                   ForumForm))

    def test_create_complete(self):
        url = reverse('pybb:forum_create', kwargs={
            'forum_id': self.parent_forum.pk
        })

        self.login_as(self.staff)

        data = {
            'name': 'My forum 2',
            'position': 1,
        }

        self.forum

        response = self.client.post(url, data=data)

        self.assertEqual(Forum.objects.count(), 3)

        forum = Forum.objects.get(name='My forum 2')

        self.assertRedirects(response,
                             forum.get_absolute_url())

        self.assertEqual(forum.name, data['name'])
        self.assertEqual(forum.position, data['position'])

    def test_update_view(self):
        url = reverse('pybb:forum_update', kwargs={
            'pk': self.forum.pk
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/forum/update.html')

        self.failUnless(isinstance(response.context['form'],
                                   ForumForm))

    def test_update_complete(self):
        url = reverse('pybb:forum_update', kwargs={
            'pk': self.forum.pk
        })

        self.login_as(self.staff)

        response = self.client.post(url, data={
            'name': 'Renamed forum',
            'position': self.forum.position
        })

        self.assertRedirects(response,
                             self.forum.get_absolute_url())

        forum = Forum.objects.get(pk=self.forum.pk)

        self.assertEqual(forum.name, 'Renamed forum')

    def test_moderators_view(self):
        url = reverse('pybb:moderator_list', kwargs={
            'pk': self.forum.pk
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/moderation/moderator/list.html')

    def test_moderator_view(self):
        self.login_as(self.staff)

        moderator = Moderator.objects.create(forum=self.forum, user=self.user)

        url = reverse('pybb:moderator_detail', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': moderator.pk
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/moderation/moderator/detail.html')

        for form in response.context['forms']:
            self.failUnless(isinstance(form, ModerationForm))

    def test_moderator_update_complete(self):
        self.login_as(self.staff)

        moderator = Moderator.objects.create(forum=self.forum, user=self.user)

        url = reverse('pybb:moderator_detail', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': moderator.pk
        })

        codenames = dict((codename, 1) for codename in defaults.PYBB_USER_PERMISSIONS + defaults.PYBB_FORUM_PERMISSIONS)

        self.assertFalse(self.user.has_perms([codename for codename in defaults.PYBB_FORUM_PERMISSIONS], self.forum))

        response = self.client.post(url, data=codenames)

        self.assertRedirects(response, url)

        self.assertTrue(self.user.has_perms([codename for codename in defaults.PYBB_FORUM_PERMISSIONS], self.forum))

    def test_moderator_create_view(self):
        url = reverse('pybb:moderator_create', kwargs={
            'forum_id': self.forum.pk,
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/moderation/moderator/create.html')

    def test_moderator_create_complete(self):
        url = reverse('pybb:moderator_create', kwargs={
            'forum_id': self.forum.pk,
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        codenames = dict((codename, 1) for codename in defaults.PYBB_USER_PERMISSIONS + defaults.PYBB_FORUM_PERMISSIONS)

        self.assertFalse(self.user.has_perms([codename for codename in defaults.PYBB_FORUM_PERMISSIONS], self.forum))

        response = self.client.post(url, data=dict(codenames, **{
            'username': self.user.username
        }))

        moderator = Moderator.objects.get(user=self.user)

        self.assertRedirects(response, reverse('pybb:moderator_detail', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': moderator.pk
        }))

        self.assertTrue(self.user.has_perms([codename for codename in defaults.PYBB_FORUM_PERMISSIONS], self.forum))

        self.assertEqual(self.forum.moderators.count(), 1)
        self.assertIn(self.user, [m for m in self.forum.moderators.all()])

    def test_moderator_delete_view(self):
        moderator = Moderator.objects.create(forum=self.forum, user=self.user)

        url = reverse('pybb:moderator_delete', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': moderator.pk
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/moderation/moderator/delete.html')

    def test_moderator_delete_complete(self):
        moderator = Moderator.objects.create(forum=self.forum, user=self.user)

        url = reverse('pybb:moderator_delete', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': moderator.pk
        })

        self.login_as(self.staff)

        response = self.client.post(url)

        self.assertRedirects(response, reverse('pybb:moderator_list', kwargs={
            'pk': self.forum.pk,
        }))

        self.assertRaises(Moderator.DoesNotExist, lambda: Moderator.objects.get(forum=self.forum, user=self.user))
        self.assertEqual(self.user.user_permissions.filter(codename__in=defaults.PYBB_USER_PERMISSIONS).count(), 0)
