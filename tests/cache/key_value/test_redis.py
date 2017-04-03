from tests.base import RedisTestCase, fixture
from .base import KeyValueTestMixin

from pybb.cache import RedisKeyValueCache


class RedisKeyValueTest(KeyValueTestMixin, RedisTestCase):

    @fixture
    def prefix(self):
        return 'test_redis_key_value'

    def get_kv_cache(self, prefix):
        """
        :rtype: pybb.cache.KeyValueCacheInterface
        """
        return RedisKeyValueCache(client=self.redis, prefix=prefix)
