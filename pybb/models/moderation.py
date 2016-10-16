from pybb.models.base import BaseLogModeration, BaseModerator, ModeratorManager, LogModerationManager


class LogModeration(BaseLogModeration):
    class Meta(BaseLogModeration.Meta):
        abstract = False

    objects = LogModerationManager()


class Moderator(BaseModerator):
    class Meta(BaseModerator.Meta):
        abstract = False

    objects = ModeratorManager()
