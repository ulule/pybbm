from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from pybb.models.base import PybbProfile

from annoying.fields import AutoOneToOneField


class Profile(PybbProfile):
    """
    Profile class that can be used if you doesn't have
    your site profile.
    """
    user = AutoOneToOneField(User, related_name='pybb_profile', verbose_name=_('User'))

    class Meta(PybbProfile.Meta):
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')
        app_label = 'pybb'

    def get_absolute_url(self):
        return reverse('pybb:user_detail', kwargs={
            'username': self.user.username
        })
