from abc import ABCMeta, abstractmethod


class KeyValueCache(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def get_bulk(self, *keys):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def set_if_not_exist(self, key, value):
        pass

    @abstractmethod
    def set_bulk(self, **kwargs):
        pass

    @abstractmethod
    def count(self):
        pass

    @abstractmethod
    def invalidate(self, key):
        pass

    @abstractmethod
    def invalidate_bulk(self, *keys):
        pass
