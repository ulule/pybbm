class BaseMarkupEngine(object):
    def __init__(self, message, obj=None):
        self.message = message
        self.obj = obj


class BaseQuoteEngine(object):
    def __init__(self, post, username):
        self.post = post
        self.username = username
