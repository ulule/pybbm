# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

from pybb import defaults

from pybb.feeds import LastPosts, LastTopics
from pybb.views import (IndexView, ForumDetailView, TopicDetailView,
                        PostsCreateView, SubscriptionListView, SubscriptionChangeView, SubscriptionDeleteView,
                        PostCreateView, PostUpdateView, PostRedirectView,
                        PostDeleteView, TopicStickView, TopicUnstickView, TopicCloseView,
                        TopicOpenView, PostModerateView, TopicPollVoteView, PostsMoveView,
                        LogModerationListView, TopicDeleteView, TopicMergeView, TopicMoveView,
                        ForumCreateView, ForumUpdateView, ModeratorListView, ModeratorCreateView,
                        ModeratorDetailView, create_subscription, UserPostsDeleteView,
                        ModeratorDeleteView, AttachmentListView, AttachmentDeleteView, TopicTrackerRedirectView,
                        UserPostsView, TopicsLatestView, ForumMarkAsReadView, post_preview)


urlpatterns = patterns(
    '',
    # Syndication feeds
    url('^feeds/posts/$',
        LastPosts(),
        name='feed_posts'),

    url('^feeds/topics/$',
        LastTopics(),
        name='feed_topics'),
)

urlpatterns += patterns(
    'pybb.views',
    # Index, Category, Forum
    url('^$',
        IndexView.as_view(),
        name='index'),

    url('^forums/(?:(?P<forum_id>\d+)/)?forums/create/$',
        ForumCreateView.as_view(),
        name='forum_create'),

    url('^forums/(?P<pk>\d+)/moderators/$',
        ModeratorListView.as_view(),
        name='moderator_list'),
    url('^forums/(?P<forum_id>\d+)/moderators/(?P<moderator_id>\d+)$',
        ModeratorDetailView.as_view(),
        name='moderator_detail'),
    url('^forums/(?P<forum_id>\d+)/moderators/(?P<moderator_id>\d+)/delete/$',
        ModeratorDeleteView.as_view(),
        name='moderator_delete'),
    url('^forums/(?P<forum_id>\d+)/moderators/create/$',
        ModeratorCreateView.as_view(),
        name='moderator_create'),
    url('^forums/update/(?P<pk>\d+)/$',
        ForumUpdateView.as_view(),
        name='forum_update'),

    url('^topics/(?P<pk>\d+)/stick/$',
        TopicStickView.as_view(),
        name='topic_stick'),
    url('^topics/(?P<pk>\d+)/unstick/$',
        TopicUnstickView.as_view(),
        name='topic_unstick'),
    url('^topics/(?P<pk>\d+)/close/$',
        TopicCloseView.as_view(),
        name='topic_close'),
    url('^topics/(?P<pk>\d+)/open/$',
        TopicOpenView.as_view(),
        name='topic_open'),
    url('^topics/merge/$',
        TopicMergeView.as_view(),
        name='topic_merge'),
    url('^topics/move/$',
        TopicMoveView.as_view(),
        name='topic_move'),
    url('^topics/(?P<pk>\d+)/delete/$',
        TopicDeleteView.as_view(),
        name='topic_delete'),
    url('^topics/(?P<pk>\d+)/poll-vote/$',
        TopicPollVoteView.as_view(),
        name='topic_poll_vote'),

    # Add topic/post
    url('^forums/(?P<forum_id>\d+)/topic/add/$',
        PostCreateView.as_view(),
        name='topic_create'),
    url('^topics/post/add/$',
        PostsCreateView.as_view(),
        name='posts_create'),
    url('^topics/(?P<topic_id>\d+)/post/add/$',
        PostCreateView.as_view(),
        name='post_create'),
    url('^topics/(?P<topic_id>\d+)/tracker/$',
        TopicTrackerRedirectView.as_view(),
        name='topic_tracker_redirect'),
    url('^topics/latest/$',
        TopicsLatestView.as_view(),
        name='topics_latest'),

    # Post
    url('^posts/redirect/(?:(?P<post_id>\d+)/)?$',
        PostRedirectView.as_view(),
        name='post_redirect'),
    url('^posts/(?P<pk>\d+)/edit/$',
        PostUpdateView.as_view(),
        name='post_update'),
    url('^posts/(?P<pk>\d+)/delete/$',
        PostDeleteView.as_view(),
        name='post_delete'),
    url('^posts/(?P<pk>\d+)/moderate/$',
        PostModerateView.as_view(),
        name='post_moderate'),
    url('^posts/move/$',
        PostsMoveView.as_view(),
        name='post_move'),

    # Subscription
    url('^subscriptions/$',
        SubscriptionListView.as_view(),
        name='subscription_list'),

    url('^subscription/topic/change/$',
        SubscriptionChangeView.as_view(),
        name='subscription_change'),

    url('^subscription/topic/delete/$',
        SubscriptionDeleteView.as_view(),
        name='subscription_delete'),

    url('^subscription/topic/add/$',
        create_subscription,
        name='subscription_create'),

    url('^post/preview/$',
        post_preview,
        name='post_preview'),

    # Commands
    url('^forums/mark-as-read/$',
        ForumMarkAsReadView.as_view(),
        name='forum_mark_as_read'),

    url('^moderation/logs/$',
        LogModerationListView.as_view(),
        name='logmoderation_list'),

    url('^(?P<username>[\w\-\_]+)/posts/$',
        UserPostsView.as_view(),
        name='user_posts'),

    url('^(?P<username>[\w\-\_]+)/posts/delete/$',
        UserPostsDeleteView.as_view(),
        name='user_posts_delete'),

    url('^(?P<slug>[\w\-\_]+)/(?:(?P<page>\d+)/)?$',
        ForumDetailView.as_view(),
        name='forum_detail'),

    url('^(?P<forum_slug>[\w\-\_]+)/(?P<pk>\d+)-(?P<slug>[\w\-\_]+)(?:\-(?P<page>\d+)/)?$',
        TopicDetailView.as_view(),
        name='topic_detail'),
)

if defaults.PYBB_ATTACHMENT_ENABLE:
    urlpatterns += patterns(
        '',
        url('^post/attachment/list/$',
            AttachmentListView.as_view(),
            name='attachment_list'),

        url('^post/attachment/(?P<pk>\d+)/delete/$',
            AttachmentDeleteView.as_view(),
            name='attachment_delete'),
    )
