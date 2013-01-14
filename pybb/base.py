from django.db import models

from pybb.mixins import OnChangeMixin, TransformManager, TransformQuerySet


class ModelBase(OnChangeMixin, models.Model):
    class Meta:
        abstract = True


class ManagerBase(TransformManager):
    pass


class QuerySetBase(TransformQuerySet):
    pass
