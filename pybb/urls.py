# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

from pybb import defaults, views, feeds


urlpatterns = patterns(
    '',
    # Syndication feeds
    url('^feeds/posts/$',
        feeds.LastPosts(),
        name='feed_posts'),

    url('^feeds/topics/$',
        feeds.LastTopics(),
        name='feed_topics'),
)

urlpatterns += patterns(
    'pybb.views',
    # Index, Category, Forum
    url('^$',
        views.IndexView.as_view(),
        name='index'),

    url('^forums/(?:(?P<forum_id>\d+)/)?forums/create/$',
        views.ForumCreateView.as_view(),
        name='forum_create'),

    url('^forums/(?P<pk>\d+)/moderators/$',
        views.ModeratorListView.as_view(),
        name='moderator_list'),
    url('^forums/(?P<forum_id>\d+)/moderators/(?P<moderator_id>\d+)$',
        views.ModeratorDetailView.as_view(),
        name='moderator_detail'),
    url('^forums/(?P<forum_id>\d+)/moderators/(?P<moderator_id>\d+)/delete/$',
        views.ModeratorDeleteView.as_view(),
        name='moderator_delete'),
    url('^forums/(?P<forum_id>\d+)/moderators/create/$',
        views.ModeratorCreateView.as_view(),
        name='moderator_create'),
    url('^forums/update/(?P<pk>\d+)/$',
        views.ForumUpdateView.as_view(),
        name='forum_update'),

    url('^topics/(?P<pk>\d+)/stick/$',
        views.TopicStickView.as_view(),
        name='topic_stick'),
    url('^topics/(?P<pk>\d+)/unstick/$',
        views.TopicUnstickView.as_view(),
        name='topic_unstick'),
    url('^topics/(?P<pk>\d+)/close/$',
        views.TopicCloseView.as_view(),
        name='topic_close'),
    url('^topics/(?P<pk>\d+)/open/$',
        views.TopicOpenView.as_view(),
        name='topic_open'),
    url('^topics/merge/$',
        views.TopicMergeView.as_view(),
        name='topic_merge'),
    url('^topics/move/$',
        views.TopicMoveView.as_view(),
        name='topic_move'),
    url('^topics/(?P<pk>\d+)/delete/$',
        views.TopicDeleteView.as_view(),
        name='topic_delete'),
    url('^topics/(?P<pk>\d+)/poll-vote/$',
        views.TopicPollVoteView.as_view(),
        name='topic_poll_vote'),

    # Add topic/post
    url('^forums/(?:(?P<forum_id>\d+)/)?topic/add/$',
        views.PostCreateView.as_view(),
        name='topic_create'),
    url('^topics/post/add/$',
        views.PostsCreateView.as_view(),
        name='posts_create'),
    url('^topics/(?P<topic_id>\d+)/post/add/$',
        views.PostCreateView.as_view(),
        name='post_create'),
    url('^topics/(?P<topic_id>\d+)/tracker/$',
        views.TopicTrackerRedirectView.as_view(),
        name='topic_tracker_redirect'),
    url('^topics/latest/$',
        views.TopicsLatestView.as_view(),
        name='topics_latest'),

    # Post
    url('^posts/redirect/(?:(?P<post_id>\d+)/)?$',
        views.PostRedirectView.as_view(),
        name='post_redirect'),
    url('^posts/(?P<pk>\d+)/edit/$',
        views.PostUpdateView.as_view(),
        name='post_update'),
    url('^posts/(?P<pk>\d+)/delete/$',
        views.PostDeleteView.as_view(),
        name='post_delete'),
    url('^posts/(?P<pk>\d+)/moderate/$',
        views.PostModerateView.as_view(),
        name='post_moderate'),
    url('^posts/move/$',
        views.PostsMoveView.as_view(),
        name='post_move'),

    # Subscription
    url('^subscriptions/$',
        views.SubscriptionListView.as_view(),
        name='subscription_list'),

    url('^subscription/topic/change/$',
        views.SubscriptionChangeView.as_view(),
        name='subscription_change'),

    url('^subscription/topic/delete/$',
        views.SubscriptionDeleteView.as_view(),
        name='subscription_delete'),

    url('^subscription/topic/add/$',
        views.create_subscription,
        name='subscription_create'),

    url('^post/preview/$',
        views.post_preview,
        name='post_preview'),

    # Commands
    url('^forums/mark-as-read/$',
        views.ForumMarkAsReadView.as_view(),
        name='forum_mark_as_read'),

    url('^moderation/logs/$',
        views.LogModerationListView.as_view(),
        name='logmoderation_list'),

    url('^(?P<username>[\w\-\_]+)/posts/$',
        views.UserPostsView.as_view(),
        name='user_posts'),

    url('^(?P<username>[\w\-\_]+)/posts/delete/$',
        views.UserPostsDeleteView.as_view(),
        name='user_posts_delete'),

    url(views.TopicDetailView.url,
        views.TopicDetailView.as_view(),
        name='topic_detail'),

    url('^(?P<slug>[\w\-\_]+)/(?:(?P<page>\d+)/)?$',
        views.ForumDetailView.as_view(),
        name='forum_detail'),
)

if defaults.PYBB_ATTACHMENT_ENABLE:
    urlpatterns += patterns(
        '',
        url('^post/attachment/list/$',
            views.AttachmentListView.as_view(),
            name='attachment_list'),

        url('^post/attachment/(?P<pk>\d+)/delete/$',
            views.AttachmentDeleteView.as_view(),
            name='attachment_delete'),
    )
