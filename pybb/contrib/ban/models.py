from django.contrib.auth.models import AnonymousUser

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import signals

from pybb.base import ModelBase, ManagerBase

from .util import get_ip
from . import settings

from pybb.compat import AUTH_USER_MODEL


class BannedUser(ModelBase):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='banned', on_delete=models.CASCADE)
    reason = models.TextField(_('Reason'), null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'pybb'
        verbose_name = _('Banned user')
        verbose_name_plural = _('Banned users')

    def __str__(self):
        return _('User %(user)s banned for %(reason)s') % {
            'user': self.user,
            'reason': self.reason
        }


class IPAddressManager(ManagerBase):
    def register(self, user, ip_address):
        params = {
            'user': user,
            'ip_address': ip_address
        }

        try:
            ip = self.model.objects.filter(**params)[0]
        except IndexError:
            ip = self.model.objects.create(**params)

        return ip


class IPAddress(ModelBase):
    user = models.ForeignKey(AUTH_USER_MODEL,
                             related_name='ip_addresses',
                             null=True, blank=True, on_delete=models.SET(AnonymousUser))
    ip_address = models.IPAddressField(_('IP Address'),
                                       help_text=_('The IP address'))

    banned = models.BooleanField(default=False, db_index=True)

    objects = IPAddressManager()

    class Meta:
        app_label = 'pybb'
        verbose_name = _('IP')
        verbose_name_plural = _('IPs')

    def __str__(self):
        return self.ip_address


def handle_user_logged_in(sender, request, user, **kwargs):
    from pybb.compat import get_user_model

    User = get_user_model()

    try:
        BannedUser.objects.get(user=user)
    except BannedUser.DoesNotExist:
        value = request.COOKIES.get(settings.PYBB_BAN_COOKIE_NAME, None)

        banned_user = None

        if value:
            try:
                existing_user = User.objects.get(pk=int(value))
            except (User.DoesNotExist, ValueError):
                banned_user = BannedUser(user=user,
                                         reason=_('Cookie exists: user already banned from anonymous account'))
            else:
                banned_user = BannedUser(user=user,
                                         reason=_('Cookie exists: user already banned for the account %s') % existing_user)

        ip_address = get_ip(request)

        exists = IPAddress.objects.filter(ip_address=ip_address, banned=True).exists()

        if exists:
            banned_user = BannedUser(user=user,
                                     reason=_('IP Address %s is banned') % ip_address)

        if banned_user:
            banned_user.save()


from django.apps import apps

if apps.ready:
    from .compat import User

    signals.user_logged_in.connect(handle_user_logged_in, sender=User)
