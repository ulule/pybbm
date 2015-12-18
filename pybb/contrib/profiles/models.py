from __future__ import unicode_literals

import django

from django.db import models
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models.signals import post_save

from pybb import defaults
from pybb.constants import TZ_CHOICES
from pybb.base import ModelBase
from pybb.processors import markup
from pybb.compat import AUTH_USER_MODEL
from pybb.fields import CAStorage

try:
    from sorl.thumbnail import ImageField
except ImportError:
    ImageField = models.ImageField


class Profile(ModelBase):
    """
    Profile class that can be used if you doesn't have
    your site profile.
    """
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='pybb_profile', verbose_name=_('User'))

    signature = models.TextField(_('Signature'), blank=True,
                                 max_length=defaults.PYBB_SIGNATURE_MAX_LENGTH)
    time_zone = models.FloatField(_('Time zone'), choices=TZ_CHOICES,
                                  default=float(defaults.PYBB_DEFAULT_TIME_ZONE))
    language = models.CharField(_('Language'), max_length=10, blank=True,
                                choices=settings.LANGUAGES,
                                default=dict(settings.LANGUAGES)[settings.LANGUAGE_CODE.split('-')[0]],
                                db_index=True)
    show_signature = models.BooleanField(_('Show signature'), blank=True,
                                         default=True, db_index=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0, db_index=True)
    avatar = ImageField(_('Avatar'), blank=True, null=True,
                        storage=CAStorage(),
                        upload_to='pybb/avatars')
    autosubscribe = models.BooleanField(_('Automatically subscribe'),
                                        help_text=_('Automatically subscribe to topics that you answer'),
                                        default=defaults.PYBB_DEFAULT_AUTOSUBSCRIBE,
                                        db_index=True)
    is_banned = models.BooleanField(default=False, db_index=True)

    class Meta(object):
        permissions = (
            ('can_define_password', _('Can define user password')),
            ('can_ban_user', _('Can ban user')),
            ('can_unban_user', _('Can unban user')),
            ('can_change_signature', _('Can change signature')),
            ('can_change_avatar', _('Can change avatar')),
        )

        app_label = 'pybb'
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def save(self, *args, **kwargs):
        self.signature = markup(self.signature, obj=self)

        super(Profile, self).save(*args, **kwargs)

    @property
    def avatar_url(self):
        try:
            return self.avatar.url
        except:
            return defaults.PYBB_DEFAULT_AVATAR_URL

    def get_absolute_url(self):
        return reverse('pybb:user_detail', kwargs={
            'username': self.user.username
        })


def get_user_timezone(user):
    return user.pybb_profile.timezone or defaults.PYBB_DEFAULT_TIME_ZONE


def user_saved(instance, created, **kwargs):
    if not created:
        return

    try:
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'pybb', 'post')
        add_topic_permission = Permission.objects.get_by_natural_key('add_topic', 'pybb', 'topic')
    except ObjectDoesNotExist:
        return

    instance.user_permissions.add(add_post_permission, add_topic_permission)
    instance.save()

    get_profile(instance)


def get_profile(user):
    try:
        return user.pybb_profile
    except ObjectDoesNotExist:
        return Profile(user=user).save()


if django.VERSION < (1, 7):
    from pybb.compat import get_user_model

    post_save.connect(user_saved, sender=get_user_model())
else:
    from django.apps import apps

    if apps.ready:
        from pybb.compat import get_user_model

        post_save.connect(user_saved, sender=get_user_model())
