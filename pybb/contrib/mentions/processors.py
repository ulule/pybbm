import re

from django.contrib.auth.models import User

from pybb.processors import BaseProcessor

from . import settings


class MentionProcessor(BaseProcessor):
    username_re = r'@([\w\-]+)'
    format = '@%(username)s'
    tag = '[mention=%(user_id)s]%(username)s[/mention]'
    model = User

    def get_user_url(self, user):
        return settings.PYBB_MENTIONS_USER_URL(user)

    def get_users(self, username_list):
        return self.model.objects.filter(username__in=username_list).values_list('username', 'id')

    def _format(self, user, body):
        username, user_id = user

        format = self.format % {
            'username': username
        }

        body = body.replace(format, self.tag % {
            'user_id': user_id,
            'username': username
        })

        return body

    def render(self):
        body = self.body

        username_list = [m.group(1) for m in re.finditer(self.username_re,
                                                         body,
                                                         re.MULTILINE)]

        users = self.get_users(username_list)

        for user in users:
            body = self._format(user, body)

        return body
