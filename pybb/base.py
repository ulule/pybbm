from django.db import models

from pybb.compat import SiteProfileNotAvailable
from pybb.mixins import OnChangeMixin, TransformManager, TransformQuerySet
from pybb.util import get_profile_model


class ModelBase(OnChangeMixin, models.Model):
    class Meta:
        abstract = True


class ManagerBase(TransformManager):
    pass


class QuerySetBase(TransformQuerySet):
    def prefetch_profiles(self, *args):
        try:
            Profile = get_profile_model()
        except SiteProfileNotAvailable:
            return self
        else:
            profile_keys = ['{}__{}'.format(prefix, Profile.user.field.related_query_name()) for prefix in args]
            return self.prefetch_related(*profile_keys)
