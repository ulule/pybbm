from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import signals

from pybb.base import ModelBase, ManagerBase
from pybb.contrib.ban.util import get_ip
from pybb.contrib.ban import settings
from pybb.compat import User


class BannedUserManager(ManagerBase):
    def contribute_to_class(self, cls, name):
        signals.user_logged_in.connect(self.user_logged_in, sender=User)
        return super(BannedUserManager, self).contribute_to_class(cls, name)

    def user_logged_in(self, sender, request, user, **kwargs):
        try:
            self.model.objects.get(user=user)
        except self.model.DoesNotExist:
            value = request.COOKIES.get(settings.PYBB_BAN_COOKIE_NAME, None)

            banned_user = None

            if value:
                try:
                    existing_user = User.objects.get(pk=int(value))
                except (User.DoesNotExist, ValueError):
                    banned_user = self.model(user=user,
                                             reason=_(u'Cookie exists: user already banned from anonymous account'))
                else:
                    banned_user = self.model(user=user,
                                             reason=_(u'Cookie exists: user already banned for the account %s') % existing_user)

            ip_address = get_ip(request)

            exists = IPAddress.objects.filter(ip_address=ip_address, banned=True).exists()

            if exists:
                banned_user = self.model(user=user,
                                         reason=_('IP Address %s is banned') % ip_address)

            if banned_user:
                banned_user.save()


class BannedUser(ModelBase):
    user = models.OneToOneField(User, related_name='banned')
    reason = models.TextField(_('Reason'), null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = BannedUserManager()

    class Meta:
        app_label = 'pybb'
        verbose_name = _('Banned user')
        verbose_name_plural = _('Banned users')

    def __unicode__(self):
        return _(u'User %(user)s banned for %(reason)s') % {
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
    user = models.ForeignKey(User,
                             related_name='ip_addresses',
                             null=True, blank=True)
    ip_address = models.IPAddressField(_('IP Address'),
                                       help_text=_('The IP address'))

    banned = models.BooleanField(default=False, db_index=True)

    objects = IPAddressManager()

    class Meta:
        app_label = 'pybb'
        verbose_name = _('IP')
        verbose_name_plural = _('IPs')

    def __unicode__(self):
        return self.ip_address
