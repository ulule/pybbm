from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import signals
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from pybb.util import tznow
from pybb.compat import AUTH_USER_MODEL
from pybb.models import Post
from pybb.base import ManagerBase, ModelBase


class ReportMessageManager(ManagerBase):
    def contribute_to_class(self, cls, name):
        signals.post_delete.connect(self.post_delete, sender=cls)
        signals.post_save.connect(self.post_save, sender=cls)
        return super(ReportMessageManager, self).contribute_to_class(cls, name)

    def post_save(self, instance, **kwargs):
        if kwargs.get('created', False):
            instance.report.compute()

    def post_delete(self, instance, **kwargs):
        instance.report.compute()


class ReportManager(ManagerBase):
    def status_new(self):
        return self.get_query_set().filter(status=self.model.STATUS_NEW)


class Report(ModelBase):
    STATUS_NEW = 0
    STATUS_CLOSED = 1

    STATUS_CHOICES = (
        (STATUS_NEW, _('New')),
        (STATUS_CLOSED, _('Closed'))
    )

    post = models.ForeignKey(Post, related_name='reports', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    message_count = models.PositiveSmallIntegerField(default=0, db_index=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                              default=STATUS_NEW,
                                              db_index=True)

    class Meta:
        app_label = 'pybb'
        verbose_name = _('Reports')
        verbose_name_plural = _('Reports')

    def compute(self, commit=True):
        self.updated = tznow()
        self.message_count = self.reported_messages.count()

        if self.is_status_closed():
            self.status = self.STATUS_NEW

        if commit:
            self.save()

    def is_status_new(self):
        return self.status == self.STATUS_NEW

    def is_status_closed(self):
        return self.status == self.STATUS_CLOSED

    def close(self, commit=True):
        self.status = self.STATUS_CLOSED

        if commit:
            self.save()

    def get_absolute_url(self):
        return reverse('report_detail', args=[self.pk])

    def __str__(self):
        return _('Reports for %s') % self.post


class ReportMessage(ModelBase):
    report = models.ForeignKey(Report, related_name='reported_messages', on_delete=models.CASCADE)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='reported_messages', on_delete=models.SET(AnonymousUser))
    message = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = ReportMessageManager()

    class Meta:
        app_label = 'pybb'
        verbose_name = _('Report message')
        verbose_name_plural = _('Report messages')
