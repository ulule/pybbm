from pybb.models.base import BaseLogModeration, BaseModerator


class LogModeration(BaseLogModeration):
    class Meta(BaseLogModeration.Meta):
        abstract = False


class Moderator(BaseModerator):
    class Meta(BaseModerator.Meta):
        abstract = False
