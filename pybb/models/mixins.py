from itertools import chain
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import signals
from django.utils.functional import cached_property

from pybb.base import ModelBase


class ParentForumQuerysetMixin(object):
    def has_parent_forum(self, forum):
        return self.filter(forum_ids__contains=[forum.id])


class ParentForumManagerMixin(object):
    def get_queryset(self):
        return ParentForumQuerysetMixin(self.model)

    def has_parent_forum(self, *args, **kwargs):
        return self.get_queryset().has_parent_forum(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        signals.pre_save.connect(self.parent_forums_pre_save, sender=cls)
        signals.post_save.connect(self.parent_forums_post_save, sender=cls)
        return super(ParentForumManagerMixin, self).contribute_to_class(cls, name)

    def parent_forums_pre_save(self, sender, instance, **kwargs):
        if ((instance.forum_ids and instance.forum_ids[0] == instance.forum_id) or
                (not instance.forum_ids and not instance.forum_id)):
            instance._has_moved = False
            return

        instance.rebuild_parent_forum_ids(commit=False)
        instance._has_moved = True

    @transaction.atomic
    def parent_forums_post_save(self, sender, instance, **kwargs):
        from pybb.models import Forum, Topic

        if not (sender == Forum and instance._has_moved):
            return

        forums = [instance]
        while forums:
            for forum in forums:
                forum_ids = [forum.id] + forum.forum_ids
                self.filter(forum=forum).all().update(forum_ids=forum_ids)
                Topic.objects.filter(forum=forum).all().update(forum_ids=forum_ids)

            forums = self.filter(forum__in=forums)

        instance._has_moved = False

    def lookup_parent_forums(self, qs):
        from pybb.models import Forum
        objects = qs.all()

        for obj in objects:
            if (obj.forum_ids and obj.forum_ids[0] != obj.forum_id) or (not obj.forum_ids and obj.forum_id):
                obj.rebuild_parent_forum_ids(commit=True)

        parent_forum_ids = set(chain([obj.forum_ids for obj in objects]))
        parent_forums = Forum.objects.filter(id__in=parent_forum_ids).all()
        parent_forums_by_id = {forum.id: forum for forum in parent_forums}

        for obj in objects:
            obj._populate_parent_forums(parent_forums_by_id)


class ParentForumBase(ModelBase):

    class Meta(object):
        abstract = True

    forum_ids = ArrayField(models.IntegerField(), blank=True, null=False, default=list)

    def __init__(self, *args, **kwargs):
        super(ParentForumBase, self).__init__(*args, **kwargs)
        self._has_moved = False

    @cached_property
    def parents(self):
        """
        Used in templates for breadcrumb building
        """
        return self.forum.parents + [self.forum, ] if self.forum_id else []

    def rebuild_parent_forum_ids(self, commit=False):
        parent_forum = self.forum
        parent_forum_ids = []
        while parent_forum:
            parent_forum_ids.append(parent_forum.id)
            parent_forum = parent_forum.forum

        self.forum_ids = parent_forum_ids

        if commit:
            self.save()

    def _populate_parent_forums(self, parent_forums_by_id):
        child = self

        while child.forum_id:
            child.forum = parent_forums_by_id[child.forum_id]
            child = child.forum

    def lookup_parent_forums(self):
        from pybb.models import Forum

        if (self.forum_ids and self.forum_ids[0] != self.forum_id) or (not self.forum_ids and self.forum_id):
            self.rebuild_parent_forum_ids(commit=True)
            return

        parent_forums_by_id = {forum.id: forum for forum in Forum.objects.filter(id__in=self.forum_ids).all()}

        self._populate_parent_forums(parent_forums_by_id)
