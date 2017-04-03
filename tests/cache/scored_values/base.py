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
        self.sv_cache.set_bulk('x1', a=1.0, b=1.1, c=1.2, d=1.3, e=1.4)
        self.sv_cache.set_bulk('x2', f=1.5, g=1.6, h=1.7, i=1.8)
        self.sv_cache.set_bulk('x3', k=2.0, l=2.1, m=2.2)

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
        assert self.sv_cache.get_range_by_index(dimension_x='x1') == [
            ('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)]

        assert self.sv_cache.get_range_by_index(dimension_x='x1', start=0, end=0) == [
            ('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)]

        assert self.sv_cache.get_range_by_index(dimension_x='x1', start=0, end=100) == [
            ('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)]

        assert self.sv_cache.get_range_by_index(dimension_x='x1', start=0, end=1) == [
            ('a', 1.0)]

        assert self.sv_cache.get_range_by_index(dimension_x='x1', start=1, end=4) == [
            ('b', 1.1), ('c', 1.2), ('d', 1.3)]

        assert self.sv_cache.get_range_by_index(dimension_x='x1', start=4, end=1) == []

        assert self.sv_cache.get_range_by_index(dimension_x='x1', start=-3, end=-1) == [
            ('c', 1.2), ('d', 1.3)]

    def test_get_range_by_score(self):
        assert self.sv_cache.get_range_by_score(from_score=1.0, to_score=1.4, dimension_x='x1') == [
            ('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)]

        assert self.sv_cache.get_range_by_score(from_score=0.0, to_score=2.0, dimension_x='x1') == [
            ('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)]

        assert self.sv_cache.get_range_by_score(from_score=1.0, to_score=1.0, dimension_x='x1') == [
            ('a', 1.0)]

        assert self.sv_cache.get_range_by_score(from_score=1.1, to_score=1.3, dimension_x='x1') == [
            ('b', 1.1), ('c', 1.2), ('d', 1.3)]

        assert self.sv_cache.get_range_by_score(from_score=1.3, to_score=1.1, dimension_x='x1') == []

    def test_get_range_by_index_all_xs(self):
        assert self.sv_cache.get_range_by_index() == {
            'x1': [('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)],
            'x2': [('f', 1.5), ('g', 1.6), ('h', 1.7), ('i', 1.8)],
            'x3': [('k', 2.0), ('l', 2.1), ('m', 2.2)]}

        assert self.sv_cache.get_range_by_index(start=0, end=1) == {
            'x1': [('a', 1.0)],
            'x2': [('f', 1.5)],
            'x3': [('k', 2.0)]}

        assert self.sv_cache.get_range_by_index(start=1, end=4) == {
            'x1': [('b', 1.1), ('c', 1.2), ('d', 1.3)],
            'x2': [('g', 1.6), ('h', 1.7), ('i', 1.8)],
            'x3': [('l', 2.1), ('m', 2.2)]}

        assert self.sv_cache.get_range_by_index(start=4, end=1) == {
            'x1': [],
            'x2': [],
            'x3': []}

        assert self.sv_cache.get_range_by_index(start=-3, end=-1) == {
            'x1': [('c', 1.2), ('d', 1.3)],
            'x2': [('g', 1.6), ('h', 1.7)],
            'x3': [('k', 2.0), ('l', 2.1)]}

    def test_get_range_by_score_all_xs(self):
        assert self.sv_cache.get_range_by_score(from_score=0, to_score=3) == {
            'x1': [('a', 1.0), ('b', 1.1), ('c', 1.2), ('d', 1.3), ('e', 1.4)],
            'x2': [('f', 1.5), ('g', 1.6), ('h', 1.7), ('i', 1.8)],
            'x3': [('k', 2.0), ('l', 2.1), ('m', 2.2)]}

        assert self.sv_cache.get_range_by_score(from_score=1.6, to_score=2.1) == {
            'x1': [],
            'x2': [('g', 1.6), ('h', 1.7), ('i', 1.8)],
            'x3': [('k', 2.0), ('l', 2.1)]}

    def test_set_score(self):
        assert self.sv_cache.get_score('x', 'y') is None

        # Create
        self.sv_cache.set_score('x', 'y', 1.5)
        assert self.sv_cache.get_score('x', 'y') == 1.5

        # Update
        self.sv_cache.set_score('x', 'y', 1.6)
        assert self.sv_cache.get_score('x', 'y') == 1.6

    def test_set_bulk(self):
        self.sv_cache.set_bulk('x1', a=2.0, b=2.1, f=2.5)
        assert self.sv_cache.get_score('x1', 'a') == 2.0
        assert self.sv_cache.get_score('x1', 'b') == 2.1
        assert self.sv_cache.get_score('x1', 'c') == 1.2
        assert self.sv_cache.get_score('x1', 'd') == 1.3
        assert self.sv_cache.get_score('x1', 'e') == 1.4
        assert self.sv_cache.get_score('x1', 'f') == 2.5

    def test_set_bulk_many_xs(self):
        self.sv_cache.set_bulk(
            x2={'f': 2.5, 'j': 1.9},
            x3={'k': 3.0})

        assert self.sv_cache.get_score('x2', 'f') == 2.5
        assert self.sv_cache.get_score('x2', 'g') == 1.6
        assert self.sv_cache.get_score('x2', 'h') == 1.7
        assert self.sv_cache.get_score('x2', 'i') == 1.8
        assert self.sv_cache.get_score('x2', 'j') == 1.9
        assert self.sv_cache.get_score('x3', 'k') == 3.0
        assert self.sv_cache.get_score('x3', 'l') == 2.1
        assert self.sv_cache.get_score('x3', 'm') == 2.2

    def test_invalidate(self):
        assert self.sv_cache.get_score('x1', 'a') == 1.0
        self.sv_cache.invalidate('x1', 'a')
        assert self.sv_cache.get_score('x1', 'a') is None

    def test_invalidate_bulk(self):
        assert self.sv_cache.get_score('x1', 'a') == 1.0
        assert self.sv_cache.get_score('x1', 'b') == 1.1
        self.sv_cache.invalidate_bulk(dimension_x='x1', dimensions_y=['a', 'b'])
        assert self.sv_cache.get_score('x1', 'a') is None
        assert self.sv_cache.get_score('x1', 'b') is None

    def test_invalidate_bulk_many_xs(self):
        assert self.sv_cache.get_score('x1', 'a') == 1.0
        assert self.sv_cache.get_score('x2', 'g') == 1.6
        self.sv_cache.invalidate_bulk(dimensions_y=['a', 'g'])
        assert self.sv_cache.get_score('x1', 'a') is None
        assert self.sv_cache.get_score('x2', 'g') is None

    def test_count(self):
        assert self.sv_cache.count('x1') == 5
        assert self.sv_cache.count('x2') == 4
        assert self.sv_cache.count('x3') == 3

    def test_count_all_xs(self):
        assert self.sv_cache.count() == 12

    def test_no_key_conflict(self):
        kv_cache_abc = self.get_sv_cache('prefix_abc')
        kv_cache_abc.set_score('x', 'y', 1.0)

        kv_cache_def = self.get_sv_cache('prefix_def')
        kv_cache_def.set_score('x', 'y', 2.0)

        assert kv_cache_abc.get_score('x', 'y') == 1.0
        assert kv_cache_def.get_score('x', 'y') == 2.0
