from django.core.urlresolvers import reverse

from pybb.tests.base import TestCase


class PreModerationTest(TestCase):
    def test_logmoderation_list_view(self):
        self.login_as(self.staff)

        response = self.client.get(reverse('pybb:logmoderation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/moderation/logs.html')
