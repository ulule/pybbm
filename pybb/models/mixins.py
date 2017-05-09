from itertools import chain
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import signals

from base import ModelBase


class ParentForumQuerysetMixin(object):
    def has_parent(self, parent):
        return self.filter(parents__contains=[parent.id])


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
        if ((instance.parents and instance.parents[0] == instance.forum_id) or
                (not instance.parents and not instance.forum_id)):
            instance._has_moved = False
            return
        parent = instance.forum
        parents = []
        while parent:
            parents.append(parent.id)
            parent = parent.forum

        instance.parents = parents
        instance._has_moved = True

    @transaction.atomic
    def parents_post_save(self, sender, instance, **kwargs):
        from pybb.models import Forum, Topic

        if not (sender == Forum and instance._has_moved):
            return

        children = list(self.has_parent(instance).all()) + list(Topic.objects.has_parent(instance).all())

        # Update parents attribute of this instance's children
        for child in children:
            idx = child.parents.index(instance.id)
            child.parents = child.parents[:idx+1] + instance.parents
            child.save(_signal=False, update_fields=('parents',))

        instance._has_moved = False

    def prefetch_parents(self, qs):
        from pybb.models import Forum
        forums = qs.all()

        parent_ids = set(chain([forum.parents for forum in forums]))
        parents = Forum.objects.filter(id__in=parent_ids).all()
        parents_by_id = {parent.id: parent for parent in parents}

        for forum in forums:
            child = forum

            while child.forum_id:
                child.forum = parents_by_id[child.forum_id]
                child = child.forum


class ParentForumBase(ModelBase):

    class Meta(object):
        abstract = True

    parents = ArrayField(models.IntegerField(), blank=True, null=False, default=list)

    def __init__(self, *args, **kwargs):
        super(ParentForumBase, self).__init__(*args, **kwargs)
        self._has_moved = False

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        return self.forum.get_parents() + [self.forum, ] if self.forum_id else []

