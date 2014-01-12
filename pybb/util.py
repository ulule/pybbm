# -*- coding: utf-8 -*-
import re
import os
import uuid
import urlparse
from collections import defaultdict

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1  # NOQA

try:
    from django.utils.timezone import timedelta
    from django.utils.timezone import now as tznow
except ImportError:
    import datetime
    from datetime import timedelta  # NOQA
    tznow = datetime.datetime.now  # NOQA

try:
    from django.views import generic
except ImportError:
    try:
        from cbv import generic  # NOQA
    except ImportError:
        raise ImportError('If you using django version < 1.3 you should install django-cbv for pybb')


from django.contrib.auth.models import SiteProfileNotAvailable
from django.conf import settings
from django.db.models import get_model
from django.core import exceptions
from django.utils.importlib import import_module
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import QueryDict
from django.shortcuts import redirect

from . import defaults


CLASS_PATH_ERROR = 'pybb is unable to interpret settings value for %s. '\
                   '%s should be in the form of a tupple: '\
                   '(\'path.to.models.Class\', \'app_label\').'


def unescape(text):
    """
    Do reverse escaping.
    """
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', '\'')


def filter_blanks(user, str):
    """
    Replace more than 3 blank lines with only 1 blank line
    """
    if user.is_staff:
        return str
    return re.sub(r'\n{2}\n+', '\n', str)


def rstrip_str(user, str):
    """
    Replace strings with spaces (tabs, etc..) only with newlines
    Remove blank line at the end
    """
    if user.is_staff:
        return str
    return '\n'.join([s.rstrip() for s in str.splitlines()])


def get_profile_model():
    """
    Return the model class for the currently-active user profile
    model, as defined by the ``AUTH_PROFILE_MODULE`` setting.

    :return: The model that is used as profile.

    """
    if (not hasattr(settings, 'AUTH_PROFILE_MODULE')) or (not settings.AUTH_PROFILE_MODULE):
        raise SiteProfileNotAvailable

    profile_mod = get_model(*settings.AUTH_PROFILE_MODULE.split('.'))

    if profile_mod is None:
        raise SiteProfileNotAvailable

    return profile_mod


def load_class(class_path, setting_name=None):
    """
    Loads a class given a class_path. The setting value may be a string or a
    tuple.

    The setting_name parameter is only there for pretty error output, and
    therefore is optional
    """
    if not isinstance(class_path, basestring):
        try:
            class_path, app_label = class_path
        except:
            if setting_name:
                raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                    setting_name, setting_name))
            else:
                raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                    'this setting', 'It'))

    try:
        class_module, class_name = class_path.rsplit('.', 1)
    except ValueError:
        if setting_name:
            txt = '%s isn\'t a valid module. Check your %s setting' % (
                class_path, setting_name)
        else:
            txt = '%s isn\'t a valid module.' % class_path
        raise exceptions.ImproperlyConfigured(txt)

    try:
        mod = import_module(class_module)
    except ImportError, e:
        if setting_name:
            txt = 'Error importing backend %s: "%s". Check your %s setting' % (
                class_module, e, setting_name)
        else:
            txt = 'Error importing backend %s: "%s".' % (class_module, e)

        raise exceptions.ImproperlyConfigured(txt)

    try:
        clazz = getattr(mod, class_name)
    except AttributeError:
        if setting_name:
            txt = ('Backend module "%s" does not define a "%s" class. Check'
                   ' your %s setting' % (class_module, class_name,
                                         setting_name))
        else:
            txt = 'Backend module "%s" does not define a "%s" class.' % (
                class_module, class_name)
        raise exceptions.ImproperlyConfigured(txt)
    return clazz


def get_model_string(model_name):
    """
    Returns the model string notation Django uses for lazily loaded ForeignKeys
    (eg 'auth.User') to prevent circular imports.

    This is needed to allow our crazy custom model usage.
    """
    setting_name = 'PYBB_%s_MODEL' % model_name.upper().replace('_', '')
    class_path = getattr(defaults, setting_name, None)

    if not class_path:
        return 'pybb.%s' % model_name
    elif isinstance(class_path, basestring):
        parts = class_path.split('.')
        try:
            index = parts.index('models') - 1
        except ValueError:
            raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                setting_name, setting_name))
        app_label, model_name = parts[index], parts[-1]
    else:
        try:
            class_path, app_label = class_path
            model_name = class_path.split('.')[-1]
        except:
            raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                setting_name, setting_name))

    return '%s.%s' % (app_label, model_name)


def queryset_to_dict(qs, key='pk', singular=True):
    """
    Given a queryset will transform it into a dictionary based on ``key``.
    """
    if singular:
        result = {}
        for u in qs:
            result.setdefault(getattr(u, key), u)
    else:
        result = defaultdict(list)
        for u in qs:
            result[getattr(u, key)].append(u)
    return result


def get_login_url():
    login_url = defaults.PYBB_LOGIN_URL

    if login_url.startswith('/'):
        return login_url

    if not callable(login_url):
        login_url = load_class(login_url)

    return login_url()


def redirect_to_login(next, login_url=None,
                      redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Redirects the user to the login page, passing the given 'next' page
    """
    if not login_url:
        login_url = get_login_url()

    login_url_parts = list(urlparse.urlparse(login_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')

    return redirect(urlparse.urlunparse(login_url_parts))


def get_file_path(instance, filename, to='pybb/avatar'):
    """
    This function generate filename with uuid4
    it's useful if:
    - you don't want to allow others to see original uploaded filenames
    - users can upload images with unicode in filenames wich can confuse browsers and filesystem
    """
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(to, filename)
