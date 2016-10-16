import os
import mimetypes

from django import test
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.contrib.auth import login
from django.conf import settings

from importlib import import_module


from pybb.models import Post, Topic, Forum
from pybb.compat import get_user_model

from exam import Exam, fixture

try:
    from lxml import html
except ImportError:
    raise Exception('PyBB requires lxml for self testing')


class FixtureMixin(Exam):
    @fixture
    def user(self):
        return get_user_model().objects.create_user('zeus', 'zeus@localhost', 'zeus')

    @fixture
    def staff(self):
        staff = get_user_model().objects.create_user('thoas', 'thoas@localhost', '$ecret')
        staff.is_staff = True
        staff.save()

        return staff

    @fixture
    def newbie(self):
        return get_user_model().objects.create_user('newbie', 'newbie@localhost', 'newbie')

    @fixture
    def superuser(self):
        superuser = get_user_model().objects.create_user('oleiade', 'oleiade@localhost', '$ecret')
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()

        return superuser

    def login_as(self, user):
        user.backend = settings.AUTHENTICATION_BACKENDS[0]

        engine = import_module(settings.SESSION_ENGINE)

        request = HttpRequest()
        if self.client.session:
            request.session = self.client.session
        else:
            request.session = engine.SessionStore()

        login(request, user)

        # Save the session values.
        request.session.save()

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.client.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.client.cookies[session_cookie].update(cookie_data)

    def login(self):
        self.login_as(self.user)

    @fixture
    def parent_forum(self):
        return Forum.objects.create(name='foo')

    @fixture
    def forum(self):
        return Forum.objects.create(name='xfoo', description='bar', forum=self.parent_forum)

    @fixture
    def topic(self):
        return Topic.objects.create(name='etopic', forum=self.forum, user=self.user)

    @fixture
    def post(self):
        return Post.objects.create(topic=self.topic, user=self.user, body='bbcode [b]test[/b]')

    def get_form_values(self, response, form='post-form', attr=None):
        if not attr:
            attr = '//form[@class="%s"]'

        return dict(html.fromstring(response.content).xpath(attr % form)[0].form_values())


class TestCase(test.TestCase, FixtureMixin):
    pass


class TransactionTestCase(test.TransactionTestCase, FixtureMixin):
    pass


def premoderate(user, post):
    """
    Test premoderate function
    Allow post without moderation for staff users only
    """
    return user.is_staff


def get_image_path(name):
    return os.path.join(os.path.dirname(__file__), 'static', 'pybb', 'img',
                        name)


def get_uploaded_file(name):
    data = open(get_image_path(name), 'rb').read()
    return SimpleUploadedFile(name, data,
                              content_type=mimetypes.guess_type(name)[0])
