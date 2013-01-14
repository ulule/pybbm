from django.test import TransactionTestCase

from pybb.tests.base import SharedTestModule
from pybb.tasks import generate_markup
from pybb.models import Post


class TasksTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()

    def test_generate_markup(self):
        generate_markup(Post._meta.db_table,
                        Post._meta.pk.column,
                        self.post.pk,
                        self.post.body)
