from django.db.models.loading import cache
cache._populate()

from django.test import TransactionTestCase

from pybb.forms import (ModerationForm, SearchUserForm, ForumForm, TopicMoveForm,
                        TopicMergeForm, get_topic_merge_formset, PostsMoveNewTopicForm,
                        PostsMoveExistingTopicForm, TopicsDeleteForm, get_topics_delete_formset)
from pybb.models import Forum, Topic, Post, TopicRedirection
from pybb.proxies import UserObjectPermission
from pybb.tests.base import SharedTestModule
from pybb import defaults

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission


class FormsTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()

        self.permissions = []

        self.content_type = ContentType.objects.get_for_model(Forum)

        self.codenames = [label for label in defaults.PYBB_FORUM_PERMISSIONS]

        self.permissions.extend(Permission.objects.filter(codename__in=self.codenames,
                                                          content_type=self.content_type))

    def test_moderation_form_with_obj(self):
        data = dict((codename, 1) for codename in self.codenames)

        form = ModerationForm(permissions=self.permissions, data=data)

        self.failUnless(form.is_valid())

        form.save(self.user, self.forum)

        self.assertTrue(self.user.has_perms(self.codenames, self.forum))

    def test_moderation_form_with_existing_permissions_and_with_obj(self):
        for permission in self.permissions:
            UserObjectPermission.objects.assign_perm(user=self.user, permission=permission, obj=self.forum)

        form = ModerationForm(permissions=self.permissions, user=self.user, obj=self.forum)

        for permission in self.permissions:
            self.assertEqual(form.fields[permission.codename].initial, 1)

    def test_moderation_form_without_obj(self):
        data = dict((codename, 1) for codename in defaults.PYBB_USER_PERMISSIONS)

        permissions = Permission.objects.filter(codename__in=data.keys())

        form = ModerationForm(permissions=permissions, data=data)

        self.failUnless(form.is_valid())

        form.save(self.user)

        self.assertTrue(self.user.has_perms(['pybb.' + value for value in data.keys()]))

    def test_moderation_form_with_existing_permissions_and_without_obj(self):
        data = dict((codename, 1) for codename in defaults.PYBB_USER_PERMISSIONS)

        permissions = Permission.objects.filter(codename__in=data.keys())

        for permission in permissions:
            self.user.user_permissions.add(permission)

        form = ModerationForm(permissions=permissions, data=data, user=self.user)

        for permission in permissions:
            self.assertEqual(form.fields[permission.codename].initial, 1)

    def test_search_user_form(self):
        data = {
            'username': self.user.username
        }

        form = SearchUserForm(data=data)

        self.failUnless(form.is_valid())

    def test_forum_form(self):
        data = {
            'name': 'test',
            'position': 1
        }

        form = ForumForm(data=data)

        self.failUnless(form.is_valid())

        data = {
            'name': 'foo',
            'position': 1
        }

        form = ForumForm(data=data)

        self.failUnless(not form.is_valid())
        self.failUnless('name' in form.errors)
        self.failUnless(form.errors['name'][0] == ForumForm.error_messages['duplicate'])

    def test_topic_merge_form(self):
        topic = Topic.objects.create(name='merged_topic', forum=self.forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='merged post')
        post.save()

        form = TopicMergeForm(topic=topic, data={
            'topic': topic.pk
        })

        self.assertFalse(form.is_valid())
        self.assertIn('topic', form.errors)

        form = TopicMergeForm(topic=topic, data={
            'topic': self.topic.pk
        })

        self.assertTrue(form.is_valid())

        new_topic = form.save()

        topic = Topic.objects.get(pk=topic.pk)

        self.assertTrue(topic.redirect)

        self.assertEqual(new_topic.redirections.count(), 1)
        self.assertEqual(Post.objects.get(pk=post.pk).topic, self.topic)
        self.assertEqual(topic.posts.count(), 0)

    def test_topic_merge_formset(self):
        topic = Topic.objects.create(name='merged_topic', forum=self.forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='merged post')
        post.save()

        topics = [topic]

        FormSet = get_topic_merge_formset(topics=topics)

        formset = FormSet()

        for i in range(len(topics)):
            self.assertEqual(formset.forms[i].topic, topics[i])

        formset = FormSet(data={
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-topic': self.topic.pk
        })

        self.assertTrue(formset.is_valid())

        for form in formset:
            new_topic = form.save()

        topic = Topic.objects.get(pk=topic.pk)

        self.assertTrue(topic.redirect)

        self.assertEqual(new_topic.redirections.count(), 1)
        self.assertEqual(Post.objects.get(pk=post.pk).topic, self.topic)
        self.assertEqual(topic.posts.count(), 0)

    def test_topic_move_form_errors(self):
        forum = Forum.objects.create(name='temporary forum')

        topic = Topic.objects.create(name='move_topic', forum=forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='move post')
        post.save()

        form = TopicMoveForm(topic=topic, data={
            'name': topic.name,
            'forum': forum.pk,
            'redirection_type': TopicRedirection.TYPE_PERMANENT_REDIRECT
        })

        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

        Topic.objects.create(name='move_topic', forum=self.forum, user=self.superuser)

        form = TopicMoveForm(topic=topic, data={
            'forum': self.forum.pk,
            'redirection_type': TopicRedirection.TYPE_PERMANENT_REDIRECT
        })

        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

        form = TopicMoveForm(topic=topic, data={
            'forum': self.forum.pk,
            'redirection_type': TopicRedirection.TYPE_EXPIRING_REDIRECT
        })

        self.assertFalse(form.is_valid())
        self.assertIn('expired', form.errors)

    def test_topic_move_form_with_new_name(self):
        forum = Forum.objects.create(name='temporary forum')

        topic = Topic.objects.create(name='move_topic', forum=forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='move post')
        post.save()

        name = 'new name for temporary topic'

        form = TopicMoveForm(topic=topic, data={
            'name': name,
            'forum': forum.pk,
            'redirection_type': TopicRedirection.TYPE_PERMANENT_REDIRECT
        })

        self.assertTrue(form.is_valid())

        new_topic = form.save()

        topic = Topic.objects.get(pk=topic.pk)

        self.assertTrue(topic.redirect)

        self.failUnless(new_topic.slug is not None)
        self.assertEqual(new_topic.redirections.count(), 1)
        self.assertEqual(Post.objects.get(pk=post.pk).topic, new_topic)
        self.assertEqual(topic.posts.count(), 0)

    def test_topic_move_form_with_new_forum(self):
        forum = Forum.objects.create(name='temporary forum')

        topic = Topic.objects.create(name='move_topic', forum=forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='move post')
        post.save()

        name = 'new name for temporary topic'

        form = TopicMoveForm(topic=topic, data={
            'name': name,
            'forum': self.forum.pk,
            'redirection_type': TopicRedirection.TYPE_PERMANENT_REDIRECT
        })

        self.assertTrue(form.is_valid())

        new_topic = form.save()

        topic = Topic.objects.get(pk=topic.pk)

        self.assertTrue(topic.redirect)

        self.failUnless(new_topic.slug is not None)
        self.assertEqual(new_topic.redirections.count(), 1)
        self.assertEqual(Post.objects.get(pk=post.pk).topic, new_topic)
        self.assertEqual(topic.posts.count(), 0)

    def test_posts_move_new_topic_form(self):
        forum = Forum.objects.create(name='temporary forum')

        topic = Topic.objects.create(name='move_topic', forum=forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='move post')
        post.save()

        posts = Post.objects.filter(id__in=[self.post.pk, post.pk])

        form = PostsMoveNewTopicForm(posts=posts, user=self.superuser, data={
            'name': 'New topic name',
            'forum': self.forum.pk,
        })

        self.assertTrue(form.is_valid())

        new_topic = form.save()

        self.assertEqual(new_topic.posts.count(), 2)

    def test_posts_move_existing_topic_form(self):
        forum = Forum.objects.create(name='temporary forum')

        topic = Topic.objects.create(name='move_topic', forum=forum, user=self.superuser)

        post = Post(topic=topic, user=self.superuser, body='move post')
        post.save()

        posts = Post.objects.filter(id__in=[post.pk])

        form = PostsMoveExistingTopicForm(posts=posts, data={
            'topic': self.topic.pk,
        })

        self.assertTrue(form.is_valid())

        form.save()

        self.assertEqual(self.topic.posts.count(), 2)

    def test_topics_delete_form(self):
        topic1 = Topic.objects.create(name='Topic 1', forum=self.forum, user=self.superuser)
        topic2 = Topic.objects.create(name='Topic 2', forum=self.forum, user=self.superuser)

        post1 = Post(topic=topic1, user=self.superuser, body='post on topic1')
        post1.save()

        post2 = Post(topic=topic2, user=self.superuser, body='post on topic2')
        post2.save()

        topics = Topic.objects.filter(pk__in=[topic1.pk, topic2.pk])

        form = TopicsDeleteForm(topics=topics, data={
            'topics': [topic1.pk, topic2.pk],
        })

        self.assertTrue(form.is_valid())

        form.save()

        topic1 = Topic.objects.get(pk=topic1.pk)
        topic2 = Topic.objects.get(pk=topic2.pk)
        post1 = Post.objects.get(pk=post1.pk)
        post2 = Post.objects.get(pk=post2.pk)

        self.assertTrue(topic1.deleted)
        self.assertTrue(topic2.deleted)
        self.assertTrue(post1.deleted)
        self.assertTrue(post2.deleted)

    def test_topics_delete_formset(self):
        topic1 = Topic.objects.create(name='Topic 1', forum=self.forum, user=self.superuser)
        topic2 = Topic.objects.create(name='Topic 2', forum=self.forum, user=self.superuser)

        post1 = Post(topic=topic1, user=self.superuser, body='post on topic1')
        post1.save()

        post2 = Post(topic=topic2, user=self.superuser, body='post on topic2')
        post2.save()

        topics = Topic.objects.filter(pk__in=[topic1.pk, topic2.pk])

        FormSet = get_topics_delete_formset(topics=topics)

        formset = FormSet(data={
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-topics': [topic1.pk, topic2.pk],
        })

        self.assertTrue(formset.is_valid())

        for form in formset:
            form.save()

        topic1 = Topic.objects.get(pk=topic1.pk)
        topic2 = Topic.objects.get(pk=topic2.pk)
        post1 = Post.objects.get(pk=post1.pk)
        post2 = Post.objects.get(pk=post2.pk)

        self.assertTrue(topic1.delete)
        self.assertTrue(topic2.delete)
        self.assertTrue(post1.deleted)
        self.assertTrue(post2.deleted)
