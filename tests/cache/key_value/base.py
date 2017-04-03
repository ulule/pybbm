from tests.base import fixture


class KeyValueTestMixin(object):
    @fixture
    def prefix(self):
        raise NotImplementedError

    def get_kv_cache(self, prefix):
        """
        :rtype: pybb.cache.KeyValueCacheInterface
        """
        raise NotImplementedError

    def setUp(self):
        super(KeyValueTestMixin, self).setUp()
        self.kv_cache.set('a', '1.0')
        self.kv_cache.set('b', '1.1')
        self.kv_cache.set('c', '1.2')

    @fixture
    def kv_cache(self):
        """
        :rtype: pybb.cache.KeyValueCacheInterface
        """
        return self.get_kv_cache(self.prefix)

    def test_get(self):
        assert self.kv_cache.get('a') == '1.0'
        assert self.kv_cache.get('b') == '1.1'
        assert self.kv_cache.get('c') == '1.2'
        assert self.kv_cache.get('d') is None

    def test_get_bulk(self):
        assert self.kv_cache.get_bulk('a', 'b', 'c') == ['1.0', '1.1', '1.2']
        assert self.kv_cache.get_bulk('a', 'c') == ['1.0', '1.2']
        assert self.kv_cache.get_bulk('a', 'b', 'c', 'd') == ['1.0', '1.1', '1.2', None]

    def test_set_if_not_exist(self):
        assert self.kv_cache.get('a') == '1.0'
        self.kv_cache.set_if_not_exist('a', '2.0')
        assert self.kv_cache.get('a') == '1.0'

        assert self.kv_cache.get('d') is None
        self.kv_cache.set_if_not_exist('d', '2.0')
        assert self.kv_cache.get('d') == '2.0'

    def test_set_score(self):
        # Create
        assert self.kv_cache.get('d') is None
        self.kv_cache.set('d', '2.0')
        assert self.kv_cache.get('d') == '2.0'

        # Update
        assert self.kv_cache.get('a') == '1.0'
        self.kv_cache.set('a', '2.0')
        assert self.kv_cache.get('a') == '2.0'

    def test_set_bulk(self):
        assert self.kv_cache.get_bulk('a', 'b', 'c', 'd') == ['1.0', '1.1', '1.2', None]
        self.kv_cache.set_bulk(a='2.0', b=2.1, c=2.2, d=2.3)
        assert self.kv_cache.get_bulk('a', 'b', 'c', 'd') == ['2.0', '2.1', '2.2', '2.3']

    def test_invalidate(self):
        assert self.kv_cache.get('b') == '1.1'
        self.kv_cache.invalidate('b')
        assert self.kv_cache.get('b') is None

    def test_invalidate_bulk(self):
        assert self.kv_cache.get_bulk('a', 'b', 'c', 'd') == ['1.0', '1.1', '1.2', None]
        self.kv_cache.invalidate_bulk('a', 'd')
        assert self.kv_cache.get_bulk('a', 'b', 'c', 'd') == [None, '1.1', '1.2', None]

    def test_count(self):
        assert self.kv_cache.count() == 3

    def test_no_key_conflict(self):
        kv_cache_abc = self.get_kv_cache('prefix_abc')
        kv_cache_abc.set('x', 'abc')

        kv_cache_def = self.get_kv_cache('prefix_def')
        kv_cache_def.set('x', 'def')

        assert kv_cache_abc.get('x') == 'abc'
        assert kv_cache_def.get('x') == 'def'
