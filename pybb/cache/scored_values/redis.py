try:
    from itertools import izip
except ImportError:
    izip = zip

from pybb.util import get_redis_connection
from .base import ScoredValueCache
from ..exception import ClientException


class RedisScoredValueCache(ScoredValueCache):

    def __init__(self, client=None, cache_alias=None, prefix=None, default_timeout=None):
        self.prefix = prefix
        self._key_pattern = '{}:*'.format(self.prefix)
        self.client = client
        self.default_timeout = default_timeout

        if not self.client and cache_alias:
            self.client = get_redis_connection(cache_alias)

        if self.client is None:
            raise ClientException('You should configure either a ``client`` parameter or ``cache_alias``')

    def _format_cache_key(self, dimension_x):
        return '{}:{}'.format(self.prefix, dimension_x)

    def _dimension_x_from_redis_key(self, redis_key):
        return redis_key[len('{}:'.format(self.prefix)):]

    @property
    def dimension_xs(self):
        return [self._dimension_x_from_redis_key(key) for key in self.client.scan_iter(match=self._key_pattern)]

    def get_score(self, dimension_x, dimension_y):
        return self.client.zscore(self._format_cache_key(dimension_x), dimension_y)

    def get_range_by_index(self, *args, **kwargs):
        pipe = self.client.pipeline(transaction=True)

        keys = list(args) + list(kwargs.keys())
        for key in keys:
            start, end = kwargs.get(key, (0, 0))
            pipe.zrange(self._format_cache_key(key), start, end - 1, withscores=True)

        results = pipe.execute()

        return {key: dict(result) for key, result in izip(keys, results)}

    def get_range_by_score(self, **kwargs):
        pipe = self.client.pipeline(transaction=True)

        keys = list(kwargs.keys())
        for key in keys:
            minimum, maximum = kwargs[key]
            pipe.zrangebyscore(self._format_cache_key(key), minimum, maximum, withscores=True)

        results = pipe.execute()

        return {key: dict(result) for key, result in izip(keys, results)}

    def set_score(self, dimension_x, dimension_y, score):
        key = self._format_cache_key(dimension_x)
        pipe = self.client.pipeline(transaction=True)

        pipe.zadd(key, **{dimension_y: score})
        if self.default_timeout:
            pipe.expire(key, self.default_timeout)

        pipe.execute()

    def set_bulk(self, **kwargs):
        pipe = self.client.pipeline(transaction=True)

        for dimension_x, score_by_dim_y in kwargs.iteritems():
            key = self._format_cache_key(dimension_x)

            pipe.zadd(key, **score_by_dim_y)
            if self.default_timeout:
                pipe.expire(key, self.default_timeout)

        pipe.execute()

    def count(self, *args, **kwargs):
        pipe = self.client.pipeline(transaction=True)

        for key in args:
            pipe.zcard(self._format_cache_key(key))

        for key, (minimum, maximum) in kwargs.iteritems():
            pipe.zcount(self._format_cache_key(key), minimum, maximum)

        results = pipe.execute()

        return sum(results)

    def invalidate(self, dimension_x, dimension_y):
        self.client.zrem(self._format_cache_key(dimension_x), dimension_y)

    def invalidate_bulk(self, **kwargs):
        pipe = self.client.pipeline(transaction=True)

        for key, values in kwargs.iteritems():
            pipe.zrem(self._format_cache_key(key), *values)

        pipe.execute()
