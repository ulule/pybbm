from collections import defaultdict

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import signals
from django.utils.translation import gettext_lazy as _

from pybb.models import Post
from pybb.compat import AUTH_USER_MODEL
from pybb.base import ModelBase, ManagerBase

from .signals import mentioned


class MentionManager(ManagerBase):
    def __init__(self, *args, **kwargs):
        super(MentionManager, self).__init__(*args, **kwargs)

        self._registry = defaultdict(list)

    def contribute_to_class(self, cls, name):
        mentioned.connect(self.mentioned)
        signals.post_save.connect(self.post_save, sender=Post)
        return super(MentionManager, self).contribute_to_class(cls, name)

    def mentioned(self, user, post, **kwargs):
        obj = {
            'from_user': post.user,
            'to_user': user,
            'post': post
        }

        self._registry[id(post)].append(obj)

    def post_save(self, instance, **kwargs):
        mentions = self._registry.pop(id(instance), [])

        for mention in mentions:
            mention['post'] = instance

            obj, created = self.model.objects.get_or_create(**mention)


class Mention(ModelBase):
    from_user = models.ForeignKey(AUTH_USER_MODEL, related_name='sent_mentions', on_delete=models.SET(AnonymousUser))
    post = models.ForeignKey(Post, related_name='mentions', on_delete=models.CASCADE)
    to_user = models.ForeignKey(AUTH_USER_MODEL, related_name='received_mentions', on_delete=models.SET(AnonymousUser))
    created = models.DateTimeField(auto_now_add=True)

    objects = MentionManager()

    class Meta:
        app_label = 'pybb'
        verbose_name = _('Mention')
        verbose_name_plural = _('Mentions')
