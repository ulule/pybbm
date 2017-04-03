from itertools import izip

from pybb.util import get_redis_connection
from .base import ScoredValueCache
from ..exception import ClientException


class RedisScoredValueCache(ScoredValueCache):

    def __init__(self, client=None, cache_alias=None, prefix=None):
        self.prefix = prefix
        self._key_pattern = '{}:*'.format(self.prefix)
        self.client = client

        if not self.client and cache_alias:
            self.client = get_redis_connection(cache_alias)

        if self.client is None:
            raise ClientException('You should configure either a ``client`` parameter or ``cache_alias``')

    def _format_cache_key(self, dimension_x):
        return '{}:{}'.format(self.prefix, dimension_x)

    def _dimension_x_from_redis_key(self, redis_key):
        return redis_key[len('{}:'.format(self.prefix)):]

    def get_score(self, dimension_x, dimension_y):
        return self.client.zscore(self._format_cache_key(dimension_x), dimension_y)

    def get_range_by_index(self, dimension_x=None, start=0, end=-1):
        if dimension_x is not None:
            return self.client.zrange(self._format_cache_key(dimension_x), start, end, withscores=True)
        else:
            keys = [key for key in self.client.scan_iter(match=self._key_pattern)]
            pipe = self.client.pipeline(transaction=True)

            for key in keys:
                pipe.zrange(key, start, end, withscores=True)
            results = pipe.execute()

            return {self._dimension_x_from_redis_key(key): result for key, result in izip(keys, results)}

    def get_range_by_score(self, from_score, to_score, dimension_x=None):
        if dimension_x is not None:
            return self.client.zrangebyscore(self._format_cache_key(dimension_x), from_score, to_score, withscores=True)
        else:
            keys = [key for key in self.client.scan_iter(match=self._key_pattern)]
            pipe = self.client.pipeline(transaction=True)

            for key in keys:
                pipe.zrangebyscore(key, from_score, to_score, withscores=True)
            results = pipe.execute()

            return {self._dimension_x_from_redis_key(key): result for key, result in izip(keys, results)}

    def set_score(self, dimension_x, dimension_y, score):
        self.client.zadd(self._format_cache_key(dimension_x), **{dimension_y: score})

    def set_bulk(self, dimension_x=None, **kwargs):
        if dimension_x is not None:
            self.client.zadd(self._format_cache_key(dimension_x), **kwargs)
        else:
            pipe = self.client.pipeline(transaction=True)
            for dimension_x, dim2_score_tuple_list in kwargs.iteritems():
                pipe.zadd(self._format_cache_key(dimension_x), **dim2_score_tuple_list)

            pipe.execute()

    def count(self, dimension_x=None, minimum=None, maximum=None):
        if dimension_x is not None:
            return self.client.zcount(self._format_cache_key(dimension_x), minimum, maximum)
        else:
            keys = [key for key in self.client.scan_iter(match=self._key_pattern)]
            pipe = self.client.pipeline(transaction=True)

            for key in keys:
                pipe.zcount(key, minimum, maximum)
            results = pipe.execute()

            return sum(results)

    def invalidate(self, dimension_x, dimension_y):
        self.client.zrem(self._format_cache_key(dimension_x), dimension_y)

    def invalidate_bulk(self, dimension_x=None, dimensions_y=()):
        """
        :type dimension_x: basestring
        :type dimensions_y: Iterable
        """
        if dimension_x is not None:
            self.client.zrem(self._format_cache_key(dimension_x), *dimensions_y)
        else:
            pipe = self.client.pipeline(transaction=True)
            for key in self.client.scan_iter(match=self._key_pattern):
                pipe.zrem(key, *dimensions_y)

            pipe.execute()
