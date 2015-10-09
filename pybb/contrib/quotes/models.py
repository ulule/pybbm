from __future__ import unicode_literals

from collections import defaultdict

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from pybb.base import ModelBase, ManagerBase
from pybb.compat import AUTH_USER_MODEL
from pybb.contrib.quotes.signals import quoted
from pybb.models import Post
from pybb import defaults
from pybb.util import load_class


class QuoteManager(ManagerBase):
    def __init__(self, *args, **kwargs):
        super(QuoteManager, self).__init__(*args, **kwargs)

        self._registry = defaultdict(list)

    def contribute_to_class(self, cls, name):
        quoted.connect(self.quoted)
        signals.post_save.connect(self.post_save, sender=Post)
        return super(QuoteManager, self).contribute_to_class(cls, name)

    def quoted(self, user, from_post, to_post, **kwargs):
        obj = {
            'to_user': to_post.user,
            'to_post': to_post,
            'from_user': user,
            'from_post': from_post
        }

        self._registry[id(from_post)].append(obj)

    def post_save(self, instance, **kwargs):
        objs = self._registry.pop(id(instance), [])

        for obj in objs:
            obj['from_post'] = instance

            quote, created = self.model.objects.get_or_create(**obj)


class Quote(ModelBase):
    from_user = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_('From user'),
                                  related_name='quotes_sent')
    from_post = models.ForeignKey(Post,
                                  related_name='quotes_sent')
    to_post = models.ForeignKey(Post, related_name='quotes_received',
                                null=True,
                                blank=True)
    to_user = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_('To user'),
                                related_name='quoted_received')
    created = models.DateTimeField(auto_now_add=True)

    objects = QuoteManager()

    class Meta:
        app_label = 'pybb'
        verbose_name = _('Quote')
        verbose_name_plural = _('Quotes')


def quote(post, username):
    return load_class(defaults.PYBB_QUOTE_ENGINE)(post, username).render()
