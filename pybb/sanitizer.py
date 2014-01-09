import bleach

from pybb.defaults import PYBB_ALLOWED_ATTRIBUTES, PYBB_ALLOWED_STYLES, PYBB_ALLOWED_TAGS

from .processors import BaseProcessor


class BleachProcessor(BaseProcessor):
    def render(self):
        return bleach.clean(self.body,
                            tags=PYBB_ALLOWED_TAGS,
                            attributes=PYBB_ALLOWED_ATTRIBUTES,
                            styles=PYBB_ALLOWED_STYLES)
