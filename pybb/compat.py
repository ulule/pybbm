import django

from django.conf import settings

__all__ = ['update_fields', 'User']

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    update_fields = lambda instance, fields: instance.save(update_fields=fields)

    from django.contrib.auth import get_user_model
else:
    update_fields = lambda instance, fields: instance.save()

    from django.contrib.auth.models import User

    def get_user_model():
        return User

if django.VERSION >= (1, 7):
    class SiteProfileNotAvailable(Exception):
        pass
else:
    from django.contrib.auth.models import SiteProfileNotAvailable  # noqa

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

try:
    import simplejson as json
except ImportError:
    import json  # noqa


def queryset(klass):
    if django.VERSION < (1, 7):
        if 'get_queryset' not in klass.__dict__:
            raise ValueError("@queryset cannot be applied "
                             "to %s because it doesn't define get_queryset()." %
                             klass.__name__)
        klass.get_query_set = klass.get_queryset

    return klass
