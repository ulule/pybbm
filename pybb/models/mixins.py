from django.db import transaction
from django.db.models import Max

from pybb.base import ManagerBase
from pybb.cache import KeyValueCacheInterface, ScoredValueCacheInterface
from pybb.util import datetime_to_timestamp, timestamp_to_datetime, tznow


class _ReadTrackerManagerMixin(object):
    _object_id_field = None  # type: str
    _user_id_field = None  # type: str
    _timestamp_field = None  # type: str

    def latest_reads(self, user, objects):
        latest_reads = self.filter(**{
            self._user_id_field: user.pk,
            '{}__in'.format(self._object_id_field): [obj.pk for obj in objects]
        }).annotate(latest=Max(self._timestamp_field)).values(self._object_id_field, 'latest')

        latest_reads.query.group_by = [self._object_id_field]

        latest_reads_by_object = {tracker[self._object_id_field]: tracker['latest'] for tracker in latest_reads.all()}

        return latest_reads_by_object


class ReadTrackerManager(_ReadTrackerManagerMixin, ManagerBase):
    class Meta:
        abstract = True

    def mark_as_read(self, user, objects):
        tracker_object_ids = [tracker[0]
                              for tracker in self.filter(**{self._user_id_field: user.pk})
                              .values_list('{}'.format(self._object_id_field))]

        trackers = []
        updated_ids = []

        for obj in objects:
            if obj.pk not in tracker_object_ids:
                trackers.append(self.model(**{
                    self._object_id_field: obj.pk,
                    self._user_id_field: user.pk
                }))
            else:
                updated_ids.append(obj.pk)

        if len(trackers):
            self.bulk_create(trackers)

        if len(updated_ids):
            self.filter(**{
                '{}__in'.format(self._object_id_field): updated_ids,
                '{}'.format(self._user_id_field): user.pk
            }).update(time_stamp=tznow())


class ReadTrackerManagerWithCache(_ReadTrackerManagerMixin, ManagerBase):
    _scored_cache = None  # type: ScoredValueCacheInterface
    _kv_store = None  # type: KeyValueCacheInterface

    _savepoint_key = None  # type: basestring

    class Meta:
        abstract = True

    # TODO: We should lock on the user key here,
    # we don't want to accidentally overwrite the user's write cache with old data from the db
    def latest_reads(self, user, objects):
        cached = {int(obj_id): timestamp_to_datetime(score)
                  for obj_id, score in self._scored_cache.get_range_by_index(dimension_1=str(user.pk))}

        missing_data = [obj for obj in objects if obj.pk not in cached.keys()]

        if not missing_data:
            return cached

        result = super(ReadTrackerManagerWithCache, self).latest_reads(user, missing_data)

        if result:
            self._scored_cache.set_score(user.pk, **result)
            result.update(cached)
            return result

        return cached

    # TODO: If we acquire lock for reads, we should do so for writes too
    def mark_as_read(self, user, objects):
        timestamp = datetime_to_timestamp(tznow())
        self._kv_store.set_if_not_exist(self._savepoint_key, str(timestamp))
        self._scored_cache.set_bulk(dimension_1=user.id, **{str(obj.id): timestamp for obj in objects})

    def save_bulk(self):
        previous_savepoint = float(self._kv_store.get(self._savepoint_key))
        now = datetime_to_timestamp(tznow())

        cached_writes = self._scored_cache.get_range_by_score(previous_savepoint, now)

        trackers = [
            self.model(**{
                self._object_id_field: int(object_id),
                self._user_id_field: int(user_id),
                self._timestamp_field: timestamp_to_datetime(timestamp)
            }) for user_id, values in cached_writes.iteritems() for object_id, timestamp in values]

        if trackers:
            with transaction.atomic():
                self.bulk_create(trackers)
                # TODO: clean old trackers
            self._kv_store.set(self._savepoint_key, str(now))
