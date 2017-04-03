from abc import ABCMeta, abstractmethod


class ScoredValueCache(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_score(self, dimension_1, dimension_2):
        pass

    @abstractmethod
    def get_range_by_index(self, start=0, end=-1, dimension_1=None):
        pass

    @abstractmethod
    def get_range_by_score(self, from_score, to_score, dimension_1=None):
        pass

    @abstractmethod
    def set_score(self, dimension_1, dimension_2, score):
        pass

    @abstractmethod
    def set_bulk(self, dimension_1=None, **kwargs):
        pass

    @abstractmethod
    def count(self, dimension_1=None, minimum=None, maximum=None):
        pass

    @abstractmethod
    def invalidate(self, dimension_1, dimension_2):
        pass

    @abstractmethod
    def invalidate_bulk(self, *args):
        pass
