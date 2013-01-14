from django.contrib.auth.models import User

from pybb.models import Post, Attachment, Topic
from pybb.util import get_profile_model, queryset_to_dict


Profile = get_profile_model()


def load_user_posts(qs, user):
    for post in qs:
        post.user = user

        if post.topic.user_id == user.pk:
            post.topic.user = user

    return qs


def lookup_topic_lastposts(qs, user=True):
    post_ids = queryset_to_dict(qs, key='last_post_id')

    posts = Post.objects.filter(pk__in=post_ids.keys())

    if user:
        posts = posts.select_related('user')

    for post in posts:
        post_ids[post.pk].last_post = post
        post_ids[post.pk].last_post.topic = post_ids[post.pk]

    return qs


def lookup_forum_lastposts(qs):
    post_ids = queryset_to_dict(qs, key='last_post_id')

    for post in Post.objects.filter(pk__in=post_ids.keys()).select_related('user', 'topic'):
        post_ids[post.pk].last_post = post
        post_ids[post.pk].last_post.topic.forum = post_ids[post.pk]

    return qs


def lookup_post_topics(qs):
    topic_ids = queryset_to_dict(qs, key='topic_id', singular=False)

    topics = queryset_to_dict(Topic.objects.filter(id__in=topic_ids.keys()).select_related('forum'))

    for topic_id, posts in topic_ids.iteritems():
        topic = None

        if topic_id in topics:
            topic = topics[topic_id]

            for post in posts:
                post.topic = topic


def lookup_users(qs):
    user_ids = queryset_to_dict(qs, key='user_id', singular=False)

    users = queryset_to_dict(User.objects.filter(id__in=user_ids.keys()))

    profiles = queryset_to_dict(Profile.objects.filter(user__in=users.keys()), key='user_id')

    for user_id, objs in user_ids.iteritems():
        if user_id in users:
            user = users[user_id]

            for obj in objs:
                obj.user = user

                if user_id in profiles:
                    obj.user._profile_cache = profiles[user_id]
                    obj.user._profile_cache.user = obj.user

        else:
            for obj in objs:
                obj.user_id = None


def lookup_post_attachments(qs):
    post_ids = queryset_to_dict(qs, key='pk')

    attachments = queryset_to_dict(Attachment.objects.filter(post__in=post_ids.keys()), key='post_id', singular=False)

    for post_id, post in post_ids.iteritems():
        if post_id in attachments:
            post_ids[post_id]._attachments = attachments[post_id]
        else:
            post_ids[post_id]._attachments = []

    return qs
