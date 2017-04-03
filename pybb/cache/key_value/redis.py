from pybb.util import get_redis_connection
from .base import KeyValueCache
from ..exception import ClientException


class RedisKeyValueCache(KeyValueCache):
    def __init__(self, client=None, cache_alias=None, prefix=None):
        self.prefix = prefix
        self.client = client

        if not self.client and cache_alias:
            self.client = get_redis_connection(cache_alias)

        if self.client is None:
            raise ClientException('You should configure either a ``client`` parameter or ``cache_alias``')

    def get(self, key):
        return self.client.hget(self.prefix, key)

    def get_bulk(self, *keys):
        return self.client.hmget(self.prefix, keys)

    def set(self, key, value):
        self.client.hset(self.prefix, key, value)

    def set_if_not_exist(self, key, value):
        self.client.hsetnx(self.prefix, key, value)

    def set_bulk(self, **kwargs):
        self.client.hmset(self.prefix, kwargs)

    def count(self):
        return self.client.hlen(self.prefix)

    def invalidate(self, key):
        self.client.hdel(self.prefix, key)

    def invalidate_bulk(self, *keys):
        self.client.hdel(self.prefix, *keys)
