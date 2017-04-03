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

    def _format_cache_key(self, dimension_1):
        return '{}:{}'.format(self.prefix, dimension_1)

    def _dimension_1_from_redis_key(self, redis_key):
        return redis_key[len('{}:'.format(self.prefix)):]

    def get_score(self, dimension_1, dimension_2):
        score = self.client.zscore(self._dimension_1_convert_in(dimension_1), self._dimension_2_convert_in(dimension_2))
        if score:
            return self._score_convert_out(score)

        return None

    def get_range_by_index(self, dimension_1=None, start=0, end=-1):
        if dimension_1 is not None:
            return self.client.zrange(self._format_cache_key(dimension_1), start, end, withscores=True)
        else:
            return {self._dimension_1_from_redis_key(key): self.client.zrange(key, start, end, withscores=True)
                    for key in self.client.scan_iter(match=self._key_pattern)}

    def get_range_by_score(self, from_score, to_score, dimension_1=None):
        if dimension_1 is not None:
            return self.client.zrangebyscore(self._format_cache_key(dimension_1), from_score, to_score, withscores=True)
        else:
            return {self._dimension_1_from_redis_key(key): self.client.zrangebyscore(key, from_score, to_score, withscores=True)
                    for key in self.client.scan_iter(match=self._key_pattern)}

    def set_score(self, dimension_1, dimension_2, score):
        self.client.zadd(self._format_cache_key(dimension_1), **{dimension_2: score})

    def set_bulk(self, dimension_1=None, **kwargs):
        if dimension_1 is not None:
            self.client.zadd(self._format_cache_key(dimension_1), **kwargs)
        else:
            for dimension_1, dim2_score_tuple_list in kwargs.iteritems():
                self.client.zadd(self._format_cache_key(dimension_1), **dim2_score_tuple_list)

    def count(self, dimension_1=None, minimum=None, maximum=None):
        if dimension_1 is not None:
            return self.client.zcount(self._format_cache_key(dimension_1), minimum, maximum)
        else:
            return sum([self.client.zcount(key, minimum, maximum)
                        for key in self.client.scan_iter(match=self._key_pattern)])

    def invalidate(self, dimension_1, dimension_2):
        self.client.zrem(self._format_cache_key(dimension_1), dimension_2)

    def invalidate_bulk(self, dimension_1, *args):
        self.client.zrem(self._format_cache_key(dimension_1), *args)
