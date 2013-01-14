from pybb import defaults


class BaseFilter(object):
    pass


class PrePostCreateFilter(object):
    def __init__(self, topic, request, forum=None):
        self.topic = topic
        self.request = request
        self.forum = forum

    def is_allowed(self, user):
        if defaults.PYBB_AUTO_USER_PERMISSIONS and not user.has_perm('pybb.add_post'):
            return False

        if defaults.PYBB_ENABLE_ANONYMOUS_POST and not user.is_authenticated():
            return True

        if user.is_authenticated() and not user.is_active:
            return False

        return True
