# -*- coding: utf-8 -*-
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden
from django.core.cache import cache

from .models import IPAddress, BannedUser
from . import settings
from .util import set_cookie, get_ip


def forbid(request, context=None):
    """
    Forbids a user to access the site
    Cleans up their session (if it exists)
    Returns a templated HttpResponseForbidden when banning requests
    Override the `403.html` template to customize the error report
    """
    for k in request.session.keys():
        del request.session[k]

    if context is None:
        context = {}

    return HttpResponseForbidden(render_to_string('pybb/ban/access_denied.html',
                                                  context,
                                                  context_instance=RequestContext(request)))


class PybbBanMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            user = request.user

            if request.COOKIES.get(settings.PYBB_BAN_COOKIE_NAME, False):
                response = forbid(request, {
                    'user': user
                })

                return response

            ip_address = get_ip(request)

            cache_key = u'%s:%s' % (ip_address, user.pk)

            if ip_address and not cache.get(cache_key, None):
                ip = IPAddress.objects.register(user,
                                                ip_address)

                cache.set(cache_key, True, settings.PYBB_BAN_CHECK_TIMEOUT)

                if settings.PYBB_BAN_FORBID_ACCESS:
                    if ip.banned or BannedUser.objects.filter(user=user).count():
                        response = forbid(request, {
                            'user': user
                        })

                        set_cookie(response,
                                   settings.PYBB_BAN_COOKIE_NAME,
                                   user.pk,
                                   settings.PYBB_BAN_COOKIE_MAX_AGE)

                        return response
