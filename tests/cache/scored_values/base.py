from tests.base import fixture


class ScoredValuesTestMixin(object):

    @fixture
    def prefix(self):
        raise NotImplementedError

    def get_sv_cache(self, prefix):
        """
        :rtype: pybb.cache.ScoredValueCacheInterface
        """
        raise NotImplementedError

    def setUp(self):
        super(ScoredValuesTestMixin, self).setUp()
        self.sv_cache.set_bulk(
            x1={'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4},
            x2={'f': 1.5, 'g': 1.6, 'h': 1.7, 'i': 1.8},
            x3={'k': 2.0, 'l': 2.1, 'm': 2.2})

    @fixture
    def sv_cache(self):
        """
        :rtype: pybb.cache.ScoredValueCacheInterface
        """
        return self.get_sv_cache(self.prefix)

    def test_get_score(self):
        assert self.sv_cache.get_score('x1', 'c') == 1.2
        assert self.sv_cache.get_score('x1', 'y') is None

    def test_get_range_by_index(self):
        assert self.sv_cache.get_range_by_index('x1') == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4}}

        assert self.sv_cache.get_range_by_index(x1=(0, 0)) == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4}}

        assert self.sv_cache.get_range_by_index(x1=(0, 100)) == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4}}

        assert self.sv_cache.get_range_by_index(x1=(0, 1)) == {
            'x1': {'a': 1.0}}

        assert self.sv_cache.get_range_by_index(x1=(1, 4)) == {
            'x1': {'b': 1.1, 'c': 1.2, 'd': 1.3}}

        assert self.sv_cache.get_range_by_index(x1=(4, 1)) == {'x1': {}}

        assert self.sv_cache.get_range_by_index(x1=(-3, -1)) == {
            'x1': {'c': 1.2, 'd': 1.3}}

    def test_get_range_by_score(self):
        assert self.sv_cache.get_range_by_score(x1=(1.0, 1.4)) == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4}}

        assert self.sv_cache.get_range_by_score(x1=(0.0, 2.0)) == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4}}

        assert self.sv_cache.get_range_by_score(x1=(1.0, 1.0)) == {
            'x1': {'a': 1.0}}

        assert self.sv_cache.get_range_by_score(x1=(1.1, 1.3)) == {
            'x1': {'b': 1.1, 'c': 1.2, 'd': 1.3}}

        assert self.sv_cache.get_range_by_score(x1=(1.3, 1.1)) == {'x1': {}}

    def test_get_range_by_index_many_xs(self):
        assert self.sv_cache.get_range_by_index('x1', 'x2', 'x3') == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4},
            'x2': {'f': 1.5, 'g': 1.6, 'h': 1.7, 'i': 1.8},
            'x3': {'k': 2.0, 'l': 2.1, 'm': 2.2}}

        assert self.sv_cache.get_range_by_index('x1', x2=(1, 2), x3=(2, 3)) == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4},
            'x2': {'g': 1.6},
            'x3': {'m': 2.2}}

        assert self.sv_cache.get_range_by_index(**{x: (1, 4) for x in ('x1', 'x2', 'x3')}) == {
            'x1': {'b': 1.1, 'c': 1.2, 'd': 1.3},
            'x2': {'g': 1.6, 'h': 1.7, 'i': 1.8},
            'x3': {'l': 2.1, 'm': 2.2}}

        assert self.sv_cache.get_range_by_index(**{x: (4, 1) for x in ('x1', 'x2', 'x3')}) == {
            'x1': {},
            'x2': {},
            'x3': {}}

        assert self.sv_cache.get_range_by_index(**{x: (-3, -1) for x in ('x1', 'x2', 'x3')}) == {
            'x1': {'c': 1.2, 'd': 1.3},
            'x2': {'g': 1.6, 'h': 1.7},
            'x3': {'k': 2.0, 'l': 2.1}}

    def test_get_range_by_score_many_xs(self):
        assert self.sv_cache.get_range_by_score(**{x: (0, 3) for x in ('x1', 'x2', 'x3')}) == {
            'x1': {'a': 1.0, 'b': 1.1, 'c': 1.2, 'd': 1.3, 'e': 1.4},
            'x2': {'f': 1.5, 'g': 1.6, 'h': 1.7, 'i': 1.8},
            'x3': {'k': 2.0, 'l': 2.1, 'm': 2.2}}

        assert self.sv_cache.get_range_by_score(**{x: (1.6, 2.1) for x in ('x1', 'x2', 'x3')}) == {
            'x1': {},
            'x2': {'g': 1.6, 'h': 1.7, 'i': 1.8},
            'x3': {'k': 2.0, 'l': 2.1}}

    def test_set_score(self):
        assert self.sv_cache.get_score('x', 'y') is None

        # Create
        self.sv_cache.set_score('x', 'y', 1.5)
        assert self.sv_cache.get_score('x', 'y') == 1.5

        # Update
        self.sv_cache.set_score('x', 'y', 1.6)
        assert self.sv_cache.get_score('x', 'y') == 1.6

    def test_set_bulk(self):
        self.sv_cache.set_bulk(x1={'a': 2.0, 'b': 2.1, 'f': 2.5})
        assert self.sv_cache.get_score('x1', 'a') == 2.0
        assert self.sv_cache.get_score('x1', 'b') == 2.1
        assert self.sv_cache.get_score('x1', 'c') == 1.2
        assert self.sv_cache.get_score('x1', 'd') == 1.3
        assert self.sv_cache.get_score('x1', 'e') == 1.4
        assert self.sv_cache.get_score('x1', 'f') == 2.5

    def test_set_bulk_many_xs(self):
        data = {
            'x4': {
                'f': 2.5,
                'j': 1.9},
            'x5': {
                'k': 3.0}}
        self.sv_cache.set_bulk(**data)
        assert self.sv_cache.get_range_by_index('x4', 'x5') == data

        data = {
            'x4': {
                'f': 3.5,
                'j': 3.9},
            'x5': {
                'k': 4.0,
                'l': 3.1}}
        self.sv_cache.set_bulk(**data)
        assert self.sv_cache.get_range_by_index('x4', 'x5') == data

    def test_invalidate(self):
        assert self.sv_cache.get_score('x1', 'a') == 1.0
        self.sv_cache.invalidate('x1', 'a')
        assert self.sv_cache.get_score('x1', 'a') is None

    def test_invalidate_bulk(self):
        assert self.sv_cache.get_score('x1', 'a') == 1.0
        assert self.sv_cache.get_score('x1', 'b') == 1.1
        self.sv_cache.invalidate_bulk(x1=('a', 'b'))
        assert self.sv_cache.get_score('x1', 'a') is None
        assert self.sv_cache.get_score('x1', 'b') is None

    def test_invalidate_bulk_many_xs(self):
        assert self.sv_cache.get_score('x1', 'a') == 1.0
        assert self.sv_cache.get_score('x2', 'g') == 1.6
        self.sv_cache.invalidate_bulk(x1=('a', 'g'), x2=('a', 'g'))
        assert self.sv_cache.get_score('x1', 'a') is None
        assert self.sv_cache.get_score('x2', 'g') is None

    def test_count(self):
        assert self.sv_cache.count('x1') == 5
        assert self.sv_cache.count('x2') == 4
        assert self.sv_cache.count('x3') == 3

        assert self.sv_cache.count(x1=(1.1, 1.3)) == 3
        assert self.sv_cache.count(x2=(1.8, 1.5)) == 0
        assert self.sv_cache.count(x3=(0, 3)) == 3

    def test_count_many_xs(self):
        assert self.sv_cache.count('x1', 'x2', 'x3') == 12
        assert self.sv_cache.count(x1=(1.1, 1.3), x2=(1.8, 1.5), x3=(0, 3)) == 6

    def test_no_key_conflict(self):
        kv_cache_abc = self.get_sv_cache('prefix_abc')
        kv_cache_abc.set_score('x', 'y', 1.0)

        kv_cache_def = self.get_sv_cache('prefix_def')
        kv_cache_def.set_score('x', 'y', 2.0)

        assert kv_cache_abc.get_score('x', 'y') == 1.0
        assert kv_cache_def.get_score('x', 'y') == 2.0
