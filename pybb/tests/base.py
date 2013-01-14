from django.core.management import call_command
from django.contrib.auth.models import User

from pybb.models import Post, Topic, Forum

__author__ = 'zeus'

try:
    from lxml import html
except ImportError:
    raise Exception('PyBB requires lxml for self testing')


class SharedTestModule(object):
    def create_user(self):
        self.user = User.objects.create_user('zeus', 'zeus@localhost', 'zeus')
        self.staff = User.objects.create_user('thoas', 'thoas@localhost', '$ecret')
        self.staff.is_staff = True
        self.staff.save()

        self.superuser = User.objects.create_user('oleiade', 'oleiade@localhost', '$ecret')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()

    def login_client(self, username='zeus', password='zeus'):
        self.client.login(username=username, password=password)

    def create_initial(self, post=True):
        self.parent_forum = Forum(name='foo')
        self.parent_forum.save()

        self.forum = Forum(name='xfoo', description='bar', forum=self.parent_forum)
        self.forum.save()
        self.topic = Topic(name='etopic', forum=self.forum, user=self.user)
        self.topic.save()
        if post:
            self.post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[/b]')
            self.post.save()

    def create_smilies(self):
        call_command('loaddata', 'smilies.json', verbosity=0)

    def get_form_values(self, response, form='post-form', attr=None):
        if not attr:
            attr = '//form[@class="%s"]'

        return dict(html.fromstring(response.content).xpath(attr % form)[0].form_values())


def premoderate(user, post):
    """
    Test premoderate function
    Allow post without moderation for staff users only
    """
    return user.username.startswith('allowed')
