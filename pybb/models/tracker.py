from pybb.models.base import BaseTopicReadTracker, BaseForumReadTracker, ForumReadTrackerManager


class TopicReadTracker(BaseTopicReadTracker):
    class Meta(BaseTopicReadTracker.Meta):
        abstract = False


class ForumReadTracker(BaseForumReadTracker):
    class Meta(BaseForumReadTracker.Meta):
        abstract = False

    objects = ForumReadTrackerManager()
