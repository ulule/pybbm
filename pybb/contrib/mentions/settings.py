from django.conf import settings
from django.core.urlresolvers import reverse

PYBB_MENTIONS_USER_URL = getattr(settings, 'PYBB_MENTIONS_USER_URL',
                                 lambda user: reverse('user_detail', args=[user.username]))

PYBB_MENTIONS_MENTION_FORMAT_WITH_USER = getattr(settings,
                                                 'PYBB_MENTIONS_MENTION_FORMAT_WITH_USER',
                                                 '@<a href="%(user_url)s" class="mention">%(username)s</a>')

PYBB_MENTIONS_MENTION_FORMAT_WITHOUT_USER = getattr(settings,
                                                    'PYBB_MENTIONS_MENTION_FORMAT_WITHOUT_USER',
                                                    '@<span class="mention">%(username)s</span>')
