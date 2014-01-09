
from django.utils.html import urlize

from pybb import defaults
from pybb.util import load_class


class BaseProcessor(object):
    def __init__(self, body, obj=None):
        self.body = body
        self.obj = obj


class UrlizeProcessor(BaseProcessor):
    def render(self):
        return urlize(self.body)


def markup(body, obj=None, context=None):
    for preprocessor in defaults.PYBB_MARKUP_PREPROCESSORS:
        body = load_class(preprocessor)(body, obj=obj).render()

    body = load_class(defaults.PYBB_MARKUP_ENGINE)(body, obj=obj).render(context)

    for postprocessor in defaults.PYBB_MARKUP_POSTPROCESSORS:
        body = load_class(postprocessor)(body, obj=obj).render()

    return body
