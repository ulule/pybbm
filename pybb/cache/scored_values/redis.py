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
            return {self._dimension_x_from_redis_key(key): self.client.zrange(key, start, end, withscores=True)
                    for key in self.client.scan_iter(match=self._key_pattern)}

    def get_range_by_score(self, from_score, to_score, dimension_x=None):
        if dimension_x is not None:
            return self.client.zrangebyscore(self._format_cache_key(dimension_x), from_score, to_score, withscores=True)
        else:
            return {self._dimension_x_from_redis_key(key): self.client.zrangebyscore(key, from_score, to_score, withscores=True)
                    for key in self.client.scan_iter(match=self._key_pattern)}

    def set_score(self, dimension_x, dimension_y, score):
        self.client.zadd(self._format_cache_key(dimension_x), **{dimension_y: score})

    def set_bulk(self, dimension_x=None, **kwargs):
        if dimension_x is not None:
            self.client.zadd(self._format_cache_key(dimension_x), **kwargs)
        else:
            for dimension_x, dim2_score_tuple_list in kwargs.iteritems():
                self.client.zadd(self._format_cache_key(dimension_x), **dim2_score_tuple_list)

    def count(self, dimension_x=None, minimum=None, maximum=None):
        if dimension_x is not None:
            return self.client.zcount(self._format_cache_key(dimension_x), minimum, maximum)
        else:
            return sum([self.client.zcount(key, minimum, maximum)
                        for key in self.client.scan_iter(match=self._key_pattern)])

    def invalidate(self, dimension_x, dimension_y):
        self.client.zrem(self._format_cache_key(dimension_x), dimension_y)

    def invalidate_bulk(self, dimension_x, *args):
        self.client.zrem(self._format_cache_key(dimension_x), *args)
