import datetime

from django.conf import settings


def set_cookie(response, key, value, max_age=None):
    if max_age is None:
        max_age = 365 * 24 * 60 * 60

    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                         "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie(key,
                        value,
                        max_age=max_age,
                        expires=expires,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)


def get_ip(request):
    """
    Gets the true client IP address of the request
    Contains proxy handling involving HTTP_X_FORWARDED_FOR and multiple addresses
    """
    ip = request.META.get('REMOTE_ADDR', None)
    if (not ip or ip == '127.0.0.1') and 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', None)

    return ip.replace(',', '').split()[0] if ip else None
