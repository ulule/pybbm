from itertools import chain
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import signals, Q
from django.utils.functional import cached_property

from pybb.base import ModelBase


class ParentForumQuerysetMixin(object):
    def children(self, forum):
        return self.filter(forum_ids__contains=[forum.id])

    def parents(self, forum):
        return self.filter(id__in=forum.forum_ids)

    def lineage(self, forum):
        """
        :return: all the parents and children of the given forum
        """
        return self.filter(
            Q(forum_ids__contains=[forum.id]) |  # children
            Q(id__in=forum.forum_ids))           # parents

    def prefetch_parent_forums(self, forum_cache_by_id=None):
        """
        Warning: this method will evaluate your queryset, use it at the very end of your filtering chain
        :return: an evaluated and populated queryset
        """
        from pybb.models import Forum

        objects = self.all()
        forum_cache_by_id = forum_cache_by_id or {}

        for obj in objects:
            if (obj.forum_ids and obj.forum_ids[0] != obj.forum_id) or (not obj.forum_ids and obj.forum_id):
                obj.rebuild_parent_forum_ids(commit=True)

        parent_forum_ids = set(chain(*[obj.forum_ids for obj in objects]))
        parent_forum_ids = [id_ for id_ in parent_forum_ids if id_ not in forum_cache_by_id]

        if parent_forum_ids:
            parent_forums = Forum.objects.filter(id__in=parent_forum_ids).all()
            forum_cache_by_id.update({forum.id: forum for forum in parent_forums})

        for obj in objects:
            obj.populate_parent_forums(forum_cache_by_id)

        return objects


class ParentForumManagerMixin(object):
    def get_queryset(self):
        return ParentForumQuerysetMixin(self.model)

    def children(self, *args, **kwargs):
        return self.get_queryset().children(*args, **kwargs)

    def parents(self, *args, **kwargs):
        return self.get_queryset().parents(*args, **kwargs)

    def lineage(self, *args, **kwargs):
        return self.get_queryset().lineage(*args, **kwargs)

    def prefetch_parent_forums(self, *args, **kwargs):
        return self.get_queryset().prefetch_parent_forums(*args, **kwargs)

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

    def populate_parent_forums(self, parent_forums_by_id):
        child = self

        while child.forum_id:
            child.forum = parent_forums_by_id[child.forum_id]
            child = child.forum

    def prefetch_parent_forums(self, forum_cache_by_id=None):
        from pybb.models import Forum

        forum_cache_by_id = forum_cache_by_id or {}

        if (self.forum_ids and self.forum_ids[0] != self.forum_id) or (not self.forum_ids and self.forum_id):
            self.rebuild_parent_forum_ids(commit=True)
            return

        forum_ids = [id_ for id_ in self.forum_ids if id_ not in forum_cache_by_id]
        if forum_ids:
            forum_cache_by_id.update({forum.id: forum for forum in Forum.objects.filter(id__in=forum_ids).all()})

        self.populate_parent_forums(forum_cache_by_id)
