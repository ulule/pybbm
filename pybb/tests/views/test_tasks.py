from pybb.tests.base import TestCase
from pybb.tasks import generate_markup


class TasksTest(TestCase):
    def test_generate_markup(self):
        generate_markup(self.post.pk)
