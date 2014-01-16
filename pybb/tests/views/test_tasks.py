from pybb.tests.base import TestCase
from pybb.tasks import generate_markup
from pybb.models import Post


class TasksTest(TestCase):
    def test_generate_markup(self):
        generate_markup(Post._meta.db_table,
                        Post._meta.pk.column,
                        self.post.pk,
                        self.post.body)
