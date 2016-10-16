# -*- coding: utf-8 -*-
import re
import hashlib
import six

from collections import defaultdict

from six.moves.urllib.parse import urlparse, urlunparse

from django.utils.timezone import now as tznow  # noqa

from django.views import generic  # noqa


from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.apps import apps
from django.core import exceptions
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import QueryDict
from django.shortcuts import redirect
from django.utils.timezone import timedelta, now as tznow  # noqa

from importlib import import_module

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
    from .compat import SiteProfileNotAvailable

    """
    Return the model class for the currently-active user profile
    model, as defined by the ``AUTH_PROFILE_MODULE`` setting.

    :return: The model that is used as profile.

    """
    if (not hasattr(settings, 'AUTH_PROFILE_MODULE')) or (not settings.AUTH_PROFILE_MODULE):
        raise SiteProfileNotAvailable

    profile_mod = apps.get_model(*settings.AUTH_PROFILE_MODULE.split('.'))

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
    if not isinstance(class_path, six.string_types):
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
    except ImportError as e:
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
    elif isinstance(class_path, six.string_types):
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

    if login_url.startswith(('/', 'http', 'https')):
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

    login_url_parts = list(urlparse(login_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')

    return redirect(urlunparse(login_url_parts))


def hash_filename(filename, digestmod=hashlib.sha1,
                  chunk_size=UploadedFile.DEFAULT_CHUNK_SIZE):

    """
    Return the hash of the contents of a filename, using chunks.

        >>> import os.path as p
        >>> filename = p.join(p.abspath(p.dirname(__file__)), 'models.py')
        >>> hash_filename(filename)
        'da39a3ee5e6b4b0d3255bfef95601890afd80709'

    """

    fileobj = File(open(filename))
    try:
        return hash_chunks(fileobj.chunks(chunk_size=chunk_size))
    finally:
        fileobj.close()


def hash_chunks(iterator, digestmod=hashlib.sha1):

    """
    Hash the contents of a string-yielding iterator.

        >>> import hashlib
        >>> digest = hashlib.sha1('abc').hexdigest()
        >>> strings = iter(['a', 'b', 'c'])
        >>> hash_chunks(strings, digestmod=hashlib.sha1) == digest
        True

    """

    digest = digestmod()
    for chunk in iterator:
        digest.update(chunk)
    return digest.hexdigest()


def shard(string, width, depth, rest_only=False):

    """
    Shard the given string by a width and depth. Returns a generator.

    A width and depth of 2 indicates that there should be 2 shards of length 2.

        >>> digest = '1f09d30c707d53f3d16c530dd73d70a6ce7596a9'
        >>> list(shard(digest, 2, 2))
        ['1f', '09', '1f09d30c707d53f3d16c530dd73d70a6ce7596a9']

    A width of 5 and depth of 1 will result in only one shard of length 5.

        >>> list(shard(digest, 5, 1))
        ['1f09d', '1f09d30c707d53f3d16c530dd73d70a6ce7596a9']

    A width of 1 and depth of 5 will give 5 shards of length 1.

        >>> list(shard(digest, 1, 5))
        ['1', 'f', '0', '9', 'd', '1f09d30c707d53f3d16c530dd73d70a6ce7596a9']

    If the `rest_only` parameter is true, only the remainder of the sharded
    string will be used as the last element:

        >>> list(shard(digest, 2, 2, rest_only=True))
        ['1f', '09', 'd30c707d53f3d16c530dd73d70a6ce7596a9']

    """

    for i in range(depth):
        yield string[(width * i):(width * (i + 1))]

    if rest_only:
        yield string[(width * depth):]
    else:
        yield string
