from pybb.models.base import BaseTopicReadTracker, BaseForumReadTracker


class TopicReadTracker(BaseTopicReadTracker):
    class Meta(BaseTopicReadTracker.Meta):
        abstract = False


class ForumReadTracker(BaseForumReadTracker):
    class Meta(BaseForumReadTracker.Meta):
        abstract = False
