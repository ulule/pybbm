from pybb.models.base import BaseAttachment


class Attachment(BaseAttachment):
    class Meta(BaseAttachment.Meta):
        abstract = False
