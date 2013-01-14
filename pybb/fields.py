from django.utils.translation import ugettext_lazy as _

from django.template.defaultfilters import filesizeformat
from django.db.models import FileField
from django.forms import forms


class ContentTypeRestrictedFileField(FileField):
    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop('content_types')
        self.max_upload_size = kwargs.pop('max_upload_size')

        super(ContentTypeRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ContentTypeRestrictedFileField, self).clean(*args, **kwargs)

        file = data.file
        content_type = file.content_type

        if not content_type in self.content_types:
            raise forms.ValidationError(_(u'Filetype %(content_type)s not supported for %(filename)s.') % {
                'content_type': content_type,
                'filename': file.name
            })

        if file._size > self.max_upload_size:
            raise forms.ValidationError(_('Please keep filesize under %(max_upload_size)s. Current filesize %(current_size)s') % {
                'max_upload_size': filesizeformat(self.max_upload_size),
                'current_size': filesizeformat(file._size)
            })

        return data
