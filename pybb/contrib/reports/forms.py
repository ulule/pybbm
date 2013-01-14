from pybb.contrib.reports.models import Report, ReportMessage

from django import forms


class ReportMessageForm(forms.ModelForm):
    class Meta:
        fields = ('message',)
        model = ReportMessage

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.post = kwargs.pop('post', None)

        super(ReportMessageForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.report, created = Report.objects.get_or_create(post=self.post)
        self.instance.user = self.user

        return super(ReportMessageForm, self).save(*args, **kwargs)
