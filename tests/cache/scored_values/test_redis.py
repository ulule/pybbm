from tests.base import RedisTestCase, fixture

from pybb.cache import RedisScoredValueCache
from .base import ScoredValuesTestMixin


class RedisScoredValuesTest(ScoredValuesTestMixin, RedisTestCase):
    """
    Timeout functionality is left untested
    """

    @fixture
    def prefix(self):
        return 'test_redis_scored_values'

    def get_sv_cache(self, prefix):
        """
        :rtype: pybb.cache.KeyValueCacheInterface
        """
        return RedisScoredValueCache(client=self.redis, prefix=prefix)
