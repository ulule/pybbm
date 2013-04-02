# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from haystack import indexes

if 'celery_haystack' in settings.INSTALLED_APPS:
    try:
        from celery_haystack.indexes import CelerySearchIndex as SearchIndex
    except ImportError:
        from haystack.indexes import SearchIndex  # NOQA
else:
    from haystack.indexes import SearchIndex  # NOQA

from pybb.models import Post, Topic


class PostIndex(SearchIndex, indexes.Indexable):
    """
    Posts indexer. The update process is customized in PostIndex.update to
    avoid querrying the database on each found post.
    """
    text = indexes.CharField(document=True, model_attr='body_text', null=True)
    body = indexes.CharField(model_attr='body')
    body_html = indexes.CharField(model_attr='body')
    post_id = indexes.IntegerField(model_attr='pk')
    created = indexes.DateTimeField(model_attr='created')
    user_id = indexes.IntegerField(model_attr='user_id')
    forum_slug = indexes.CharField()
    forum_name = indexes.CharField()
    forum_id = indexes.IntegerField()
    topic_slug = indexes.CharField()
    topic_name = indexes.CharField(null=True)
    topic_id = indexes.IntegerField(null=True)
    replies = indexes.IntegerField()
    hidden = indexes.BooleanField()
    staff = indexes.BooleanField()
    updated = indexes.DateTimeField()
    topic_breadcrumbs = indexes.MultiValueField()
    is_first_post = indexes.BooleanField()

    def prepare_forum_slug(self, obj):
        return obj.topic.forum.slug

    def prepare_forum_name(self, obj):
        return obj.topic.forum.name

    def prepare_forum_id(self, obj):
        return obj.topic.forum.pk

    def prepare_topic_slug(self, obj):
        return obj.topic.slug

    def prepare_topic_name(self, obj):
        return obj.topic.name

    def prepare_topic_id(self, obj):
        return obj.topic.pk

    def prepare_replies(self, obj):
        return obj.topic.post_count

    def prepare_hidden(self, obj):
        return obj.topic.is_hidden()

    def prepare_staff(self, obj):
        return obj.topic.forum.staff

    def prepare_updated(self, obj):
        return obj.updated or obj.created

    def prepare_topic_breadcrumbs(self, obj):
        return [t.id for t in obj.topic.get_parents()]

    def prepare_is_first_post(self, obj):
        return obj.topic.first_post_id == obj.pk

    def get_model(self):
        return Post

    def get_updated_field(self):
        return 'updated'

    def index_queryset(self, using=None):
        qs = self.read_queryset(using=using)

        if hasattr(self, 'topic'):
            qs = qs.filter(topic=self.topic)

        return qs

    def build_queryset(self, using=None, start_date=None, end_date=None):
        '''a (simplified) copy of indexes.SearchIndex to use self.read_queyset'''
        extra_lookup_kwargs = {}
        model = self.get_model()
        updated_field = self.get_updated_field()

        if start_date:
            extra_lookup_kwargs['%s__gte' % updated_field] = start_date

        if end_date:
            extra_lookup_kwargs['%s__lte' % updated_field] = end_date

        index_qs = self.read_queryset(using=using)

        if not hasattr(index_qs, 'filter'):
            raise ImproperlyConfigured("The '%r' class must return a 'QuerySet' in the 'index_queryset' method." % self)

        return index_qs.filter(**extra_lookup_kwargs).order_by(model._meta.pk.name)

    def read_queryset(self, using=None):
        """
        limit to non-deleted posts
        """
        return self.get_model().objects.filter(deleted=False)

    def update(self, using=None):
        """
        the update queryset is chunked by topic, so the topic is retrived only
        once and injected into the objects.
        """
        backend = self._get_backend(using)

        if backend is not None:
            topics = Topic.objects.visible().select_related('forum')

            for topic in topics:
                posts = topic.posts.visible()

                for post in posts:
                    post.topic = topic

                self.topic = topic

                backend.update(self, posts)
