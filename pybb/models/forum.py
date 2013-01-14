from pybb.models.base import BaseForum


class Forum(BaseForum):
    class Meta(BaseForum.Meta):
        abstract = False
