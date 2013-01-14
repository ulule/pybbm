import re

from django import forms
from django.utils.translation import ugettext_lazy as _

from pybb import defaults
from pybb.util import get_profile_model


class EditProfileForm(forms.ModelForm):
    class Meta(object):
        model = get_profile_model()
        fields = ['signature', 'time_zone', 'language',
                  'show_signature', 'avatar']

    signature = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'cols:': 60}), required=False)

    def clean_avatar(self):
        if self.cleaned_data['avatar'] and (self.cleaned_data['avatar'].size > defaults.PYBB_MAX_AVATAR_SIZE):
            raise forms.ValidationError(_('Avatar is too large, max size: %s bytes') % defaults.PYBB_MAX_AVATAR_SIZE)

        return self.cleaned_data['avatar']

    def clean_signature(self):
        value = self.cleaned_data['signature'].strip()
        if len(re.findall(r'\n', value)) > defaults.PYBB_SIGNATURE_MAX_LINES:
            raise forms.ValidationError(_('Number of lines is limited to %d') % defaults.PYBB_SIGNATURE_MAX_LINES)
        if len(value) > defaults.PYBB_SIGNATURE_MAX_LENGTH:
            raise forms.ValidationError(_('Length of signature is limited to %d') % defaults.PYBB_SIGNATURE_MAX_LENGTH)
        return value
