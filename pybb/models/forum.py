from pybb.models.base import BaseForum, ForumManager


class Forum(BaseForum):
    class Meta(BaseForum.Meta):
        abstract = False

    objects = ForumManager()
