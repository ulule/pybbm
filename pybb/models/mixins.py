from itertools import chain
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import signals
from django.utils.functional import cached_property

from base import ModelBase


class ParentForumQuerysetMixin(object):
    def has_parent(self, parent):
        return self.filter(forum_ids__contains=[parent.id])


class ParentForumManagerMixin(object):
    def get_queryset(self):
        return ParentForumQuerysetMixin(self.model)

    def has_parent(self, *args, **kwargs):
        return self.get_queryset().has_parent(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        signals.pre_save.connect(self.parents_pre_save, sender=cls)
        signals.post_save.connect(self.parents_post_save, sender=cls)
        return super(ParentForumManagerMixin, self).contribute_to_class(cls, name)

    def parents_pre_save(self, sender, instance, **kwargs):
        if ((instance.forum_ids and instance.forum_ids[0] == instance.forum_id) or
                (not instance.forum_ids and not instance.forum_id)):
            instance._has_moved = False
            return

        instance.rebuild_parents(commit=False)
        instance._has_moved = True

    @transaction.atomic
    def parents_post_save(self, sender, instance, **kwargs):
        from pybb.models import Forum, Topic

        if not (sender == Forum and instance._has_moved):
            return

        children = list(self.has_parent(instance).all()) + list(Topic.objects.has_parent(instance).all())

        # Update forum_ids attribute of this instance's children
        for child in children:
            idx = child.forum_ids.index(instance.id)
            child.forum_ids = child.forum_ids[:idx+1] + instance.forum_ids
            child.save(_signal=False, update_fields=('forum_ids',))

        instance._has_moved = False

    def lookup_parents(self, qs):
        from pybb.models import Forum
        objects = qs.all()

        for obj in objects:
            if (obj.forum_ids and obj.forum_ids[0] != obj.forum_id) or (not obj.forum_ids and obj.forum_id):
                obj.rebuild_parents(commit=True)

        parent_ids = set(chain([obj.forum_ids for obj in objects]))
        parents = Forum.objects.filter(id__in=parent_ids).all()
        parents_by_id = {parent.id: parent for parent in parents}

        for obj in objects:
            obj._populate_parents(parents_by_id)


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
        return self.forum.parents() + [self.forum, ] if self.forum_id else []

    def rebuild_parents(self, commit=False):
        parent = self.forum
        parents = []
        while parent:
            parents.append(parent.id)
            parent = parent.forum

        self.forum_ids = parents

        if commit:
            self.save()

    def _populate_parents(self, parents_by_id):
        child = self

        while child.forum_id:
            child.forum = parents_by_id[child.forum_id]
            child = child.forum

    def lookup_parents(self):
        from pybb.models import Forum

        if (self.forum_ids and self.forum_ids[0] != self.forum_id) or (not self.forum_ids and self.forum_id):
            self.rebuild_parents(commit=True)
            return

        parents_by_id = {parent.id: parent for parent in Forum.objects.filter(id__in=self.forum_ids).all()}

        self._populate_parents(parents_by_id)
