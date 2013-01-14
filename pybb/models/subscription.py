from pybb.models.base import BaseSubscription


class Subscription(BaseSubscription):
    class Meta(BaseSubscription.Meta):
        abstract = False
