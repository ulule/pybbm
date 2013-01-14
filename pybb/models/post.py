from pybb.models.base import BasePost


class Post(BasePost):
    class Meta(BasePost.Meta):
        abstract = False
