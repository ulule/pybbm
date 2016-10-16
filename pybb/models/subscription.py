from pybb.models.base import BaseSubscription, SubscriptionManager


class Subscription(BaseSubscription):
    class Meta(BaseSubscription.Meta):
        abstract = False

    objects = SubscriptionManager()
