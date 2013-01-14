from pybb.models.base import BaseTopic


class Topic(BaseTopic):
    class Meta(BaseTopic.Meta):
        abstract = False
