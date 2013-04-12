class SearchQuerySetSafeIterator(object):
    """
    Wrap a search queryset to prevent it to yield None. It only trips out
    the first None objects at the moment in __getitem__ and __len__. __iter__
    is completly safe.
    """
    def __init__(self, sqs):
        self.sqs = sqs
        self.offset = 0
        try:
            for ob in sqs:
                if not ob is None:
                    break

                self.offset += 1
        except ValueError:
            # a bug in haystack.query:122 : `if len(self) <= 0:`
            self.offset = 0
            self.sqs = []

    def __len__(self):
        len_ = len(self.sqs) - self.offset

        if len_ >= 0:
            return len_

        # this must not happen
        return 0

    def count(self):
        return len(self)

    def _shift_slice(self, k, offset):
        if isinstance(k, slice):
            return slice(k.start + offset, k.stop + offset)

        return k + offset

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not isinstance(k, (slice, int, long)):
            raise TypeError

        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), "Negative indexing is not supported."

        k = self._shift_slice(k, self.offset)

        result = self.sqs.__getitem__(k)
        if result is None:
            while result is None:
                k += 1
                result = self.sqs.__getitem__(k)
        elif isinstance(result, list):
            # TODO: replace striped results by consitent objects after the
            # original slice
            return [obj for obj in result if obj is not None]

        return result

    def __iter__(self):
        return self._iterator()

    def _iterator(self):
        for obj in self.sqs:
            if obj is not None:
                yield obj
