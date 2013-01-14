from django.test import TransactionTestCase
from django.core.urlresolvers import reverse

from pybb.tests.base import SharedTestModule


class PreModerationTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()

    def test_logmoderation_list_view(self):
        self.login_client(username='thoas', password='$ecret')

        response = self.client.get(reverse('pybb:logmoderation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/moderation/logs.html')
