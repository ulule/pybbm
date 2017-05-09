from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from pybb.contrib.ban.forms import BanForm
from pybb.contrib.ban.models import BannedUser, IPAddress, handle_user_logged_in
from pybb.contrib.ban import settings
from pybb.contrib.ban.middleware import PybbBanMiddleware

from tests.base import TestCase

from mock import patch


class BanTest(TestCase):
    def test_ban_list_view(self):
        url = reverse('ban_list')

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/ban/list.html')

    def test_ban_view(self):
        url = reverse('ban_create', kwargs={
            'username': self.user.username
        })

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/ban/create.html')

        self.failUnless(isinstance(response.context['form'],
                                   BanForm))

    def test_ban_complete(self):
        url = reverse('ban_create', kwargs={
            'username': self.user.username
        })

        self.login_as(self.staff)

        response = self.client.post(url, data={
            'reason': 'Because he is too small'
        })

        self.assertRedirects(response,
                             reverse('ban_list'))

        self.assertEqual(BannedUser.objects.filter(user=self.user).count(), 1)

    def test_ban_complete_with_ip_address(self):
        url = reverse('ban_create', kwargs={
            'username': self.user.username
        })

        self.login_as(self.staff)

        IPAddress.objects.bulk_create([
            IPAddress(user=self.user, ip_address='199.59.149.230'),
            IPAddress(user=self.user, ip_address='66.220.152.16'),
            IPAddress(user=self.user, ip_address='74.125.230.201'),
        ])

        response = self.client.get(url)

        self.assertEqual(len(response.context['form'].ip_addresses), 3)

        response = self.client.post(url, data={
            'reason': 'Because he is too small',
            'ip_address_1': 1,
            'ip_address_2': 0,
            'ip_address_3': 1,
        })

        self.assertRedirects(response,
                             reverse('ban_list'))

        self.assertEqual(BannedUser.objects.filter(user=self.user).count(), 1)
        self.assertEqual(IPAddress.objects.filter(user=self.user, banned=True).count(), 2)

    def test_ban_delete_view(self):
        url = reverse('ban_delete', kwargs={
            'username': self.user.username
        })

        self.login_as(self.staff)

        BannedUser.objects.create(user=self.user)

        IPAddress.objects.bulk_create([
            IPAddress(user=self.user, ip_address='199.59.149.230', banned=True),
            IPAddress(user=self.user, ip_address='66.220.152.16', banned=True),
            IPAddress(user=self.user, ip_address='74.125.230.201', banned=False),
        ])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/ban/delete.html')

    def test_ban_delete_complete(self):
        url = reverse('ban_delete', kwargs={
            'username': self.user.username
        })

        self.login_as(self.staff)

        BannedUser.objects.create(user=self.user)

        IPAddress.objects.bulk_create([
            IPAddress(user=self.user, ip_address='199.59.149.230', banned=True),
            IPAddress(user=self.user, ip_address='66.220.152.16', banned=True),
            IPAddress(user=self.user, ip_address='74.125.230.201', banned=False),
        ])

        response = self.client.post(url)

        self.assertRedirects(response,
                             reverse('ban_list'))

        self.assertEqual(IPAddress.objects.filter(user=self.user).filter(banned=True).count(), 0)

        self.assertRaises(BannedUser.DoesNotExist, lambda: BannedUser.objects.get(user=self.user))

    def test_reban_existing_ip_address_banned(self):
        BannedUser.objects.create(user=self.user)

        IPAddress.objects.bulk_create([
            IPAddress(user=self.user, ip_address='199.59.149.230', banned=True),
            IPAddress(user=self.user, ip_address='66.220.152.16', banned=True),
            IPAddress(user=self.user, ip_address='74.125.230.201', banned=False),
        ])

        factory = RequestFactory(REMOTE_ADDR='199.59.149.230')
        request = factory.get('/post/1')

        handle_user_logged_in(self.newbie.__class__, request, self.newbie)

        self.assertEqual(BannedUser.objects.filter(user=self.newbie).count(), 1)

    def test_reban_existing_cookie(self):
        BannedUser.objects.create(user=self.user)

        factory = RequestFactory()
        factory.cookies[settings.PYBB_BAN_COOKIE_NAME] = self.user.pk
        request = factory.get('/post/1')

        handle_user_logged_in(self.newbie.__class__, request, self.newbie)

        self.assertEqual(BannedUser.objects.filter(user=self.newbie).count(), 1)

    def test_reban_existing_fake_cookie(self):
        BannedUser.objects.create(user=self.user)

        factory = RequestFactory()
        factory.cookies[settings.PYBB_BAN_COOKIE_NAME] = self.user.pk
        request = factory.get('/post/1')

        handle_user_logged_in(self.newbie.__class__, request, self.newbie)

        self.assertEqual(BannedUser.objects.filter(user=self.newbie).count(), 1)

    def test_ban_already_banned_user(self):
        BannedUser.objects.create(user=self.user)

        factory = RequestFactory()
        factory.cookies[settings.PYBB_BAN_COOKIE_NAME] = 'h4ck0r'
        request = factory.get('/post/1')

        handle_user_logged_in(self.newbie.__class__, request, self.newbie)

        self.assertEqual(BannedUser.objects.filter(user=self.user).count(), 1)

    def test_ban_middelware(self):
        from pybb.compat import get_user_model

        with patch.object(get_user_model(), 'is_authenticated') as is_authenticated:
            is_authenticated.return_value = True

            factory = RequestFactory(REMOTE_ADDR='199.59.149.230')
            request = factory.get('/post/1')
            request.user = self.user
            request.session = {}

            middleware = PybbBanMiddleware()
            middleware.process_request(request)

            self.assertEqual(IPAddress.objects.filter(user=self.user, ip_address='199.59.149.230').count(), 1)

            ip_address = IPAddress.objects.get(user=self.user, ip_address='199.59.149.230')

            ip_address.banned = True
            ip_address.save()

            middleware = PybbBanMiddleware()
            response = middleware.process_request(request)

            self.assertEqual(int(response.cookies[settings.PYBB_BAN_COOKIE_NAME].value), self.user.pk)
