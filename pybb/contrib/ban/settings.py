from django.conf import settings

PYBB_BAN_FORBID_ACCESS = getattr(settings, 'PYBB_BAN_FORBID_ACCESS', True)

PYBB_BAN_COOKIE_NAME = getattr(settings, 'PYBB_BAN_COOKIE_NAME', 'pybb.ban')

PYBB_BAN_COOKIE_MAX_AGE = getattr(settings, 'PYBB_BAN_COOKIE_MAX_AGE', 31 * 24 * 60 * 60)  # one month

PYBB_BAN_CHECK_TIMEOUT = getattr(settings, 'PYBB_BAN_CHECK_TIMEOUT', 5 * 60)
