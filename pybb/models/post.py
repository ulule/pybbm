from pybb.models.base import BasePost, PostManager


class Post(BasePost):
    class Meta(BasePost.Meta):
        abstract = False

    objects = PostManager()
