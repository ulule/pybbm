from abc import ABCMeta, abstractmethod, abstractproperty


class ScoredValueCache(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def dimension_xs(self):
        """
        :rtype: collections.Iterable
        """
        pass

    @abstractmethod
    def get_score(self, dimension_x, dimension_y):
        pass

    @abstractmethod
    def get_range_by_index(self, *args, **kwargs):
        """
        :param args: ('x1', ...)
        :param kwargs: {'x2': (start_index, end_index), ...}
        :return: {'x1': {'y1': score1, 'y2': score2, ...}, 'x2': {'z1': score1, 'z2': score2, ...}, ...}

        Indexes are semi-inclusive, the same as everywhere else in Python

        get_range_by_index(x=(0,1)) will return 1 element (assuming it exists), just like ``my_array[0: 1]`` would

        If you want the full set or indexes up-to-and-including the end, leave the ``end`` parameter to its default (0),
        the same as you would do in Python:
            * ``my_array = [0, 1, 2]``
            * ``my_array[0:-1]`` >>> [0, 1]
            * ``my_array[0:]`` >>> [0, 1, 2]
        """
        pass

    @abstractmethod
    def get_range_by_score(self, **kwargs):
        """
        :param kwargs: {'x1': (start_score, end_score), 'x2': (start_score, end_score), ...}
        :return: {'x1': {'y1': score1, 'y2': score2, ...}, 'x2': {'z1': score1, 'z2': score2, ...}, ...}

        Scores are inclusive
        """
        pass

    @abstractmethod
    def set_score(self, dimension_x, dimension_y, score):
        pass

    @abstractmethod
    def set_bulk(self, **kwargs):
        """
        :param kwargs: {'x1': {'y1': score1, 'y2': score2, ...}, 'x2': {'z1': score1, 'z2': score2, ...}, ...}
        :return: None
        """
        pass

    @abstractmethod
    def count(self, *args, **kwargs):
        """
        :param args: ('x1', 'x2', 'x3')
        :param kwargs: {'x4': (start_score, end_score), 'x5': (start_score, end_score), ...}
        :return: int
        """
        pass

    @abstractmethod
    def invalidate(self, dimension_x, dimension_y):
        pass

    @abstractmethod
    def invalidate_bulk(self, **kwargs):
        """
        :param kwargs: {'x1': ('y1', 'y2', ...), 'x2': ('z1', 'z2', ...), ...}
        :return: None
        """
        pass
