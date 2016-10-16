from pybb.models.base import BaseTopic, TopicManager


class Topic(BaseTopic):
    class Meta(BaseTopic.Meta):
        abstract = False

    objects = TopicManager()
