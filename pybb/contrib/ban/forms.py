from django import forms
from django.utils.translation import ugettext_lazy as _

from pybb.contrib.ban.models import BannedUser, IPAddress


class BanForm(forms.ModelForm):
    class Meta:
        model = BannedUser
        fields = ('reason',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        super(BanForm, self).__init__(*args, **kwargs)

        self.fields['reason'].required = True

        if self.user:
            self.ip_addresses = IPAddress.objects.filter(user=self.user)

            for ip_address in self.ip_addresses:
                self.fields['ip_address_%d' % ip_address.pk] = forms.ChoiceField(
                    label=_('Ban IP Address %s') % ip_address.ip_address,
                    widget=forms.RadioSelect(),
                    choices=(
                        (0, _('No')),
                        (1, _('Yes')),
                    ),
                    initial=0
                )

    def save(self, *args, **kwargs):
        self.instance.user = self.user

        banned = super(BanForm, self).save(*args, **kwargs)

        banned_ips = []

        if self.ip_addresses:
            for ip in self.ip_addresses:
                value = int(self.cleaned_data['ip_address_%d' % ip.pk])

                if value:
                    ip.banned = True
                    ip.save()

                    banned_ips.append(ip)

        return banned, banned_ips
