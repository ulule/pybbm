from pybb import defaults

from pybb.util import load_class

IndexView = load_class(defaults.PYBB_INDEX_VIEW)
ForumCreateView = load_class(defaults.PYBB_FORUM_CREATE_VIEW)
ForumDetailView = load_class(defaults.PYBB_FORUM_DETAIL_VIEW)
ForumUpdateView = load_class(defaults.PYBB_FORUM_UPDATE_VIEW)
LogModerationListView = load_class(defaults.PYBB_LOG_MODERATION_VIEW)
TopicDetailView = load_class(defaults.PYBB_TOPIC_DETAIL_VIEW)
PostsMoveView = load_class(defaults.PYBB_POSTS_MOVE_VIEW)
PostCreateView = load_class(defaults.PYBB_POST_CREATE_VIEW)
PostsCreateView = load_class(defaults.PYBB_POSTS_CREATE_VIEW)
PostUpdateView = load_class(defaults.PYBB_POST_UPDATE_VIEW)
PostRedirectView = load_class(defaults.PYBB_POST_REDIRECT_VIEW)
PostModerateView = load_class(defaults.PYBB_POST_MODERATE_VIEW)
PostDeleteView = load_class(defaults.PYBB_POST_DELETE_VIEW)
TopicDeleteView = load_class(defaults.PYBB_TOPIC_DELETE_VIEW)
TopicsDeleteView = load_class(defaults.PYBB_TOPICS_DELETE_VIEW)
TopicStickView = load_class(defaults.PYBB_TOPIC_STICK_VIEW)
TopicUnstickView = load_class(defaults.PYBB_TOPIC_UNSTICK_VIEW)
TopicCloseView = load_class(defaults.PYBB_TOPIC_CLOSE_VIEW)
TopicMergeView = load_class(defaults.PYBB_TOPIC_MERGE_VIEW)
TopicMoveView = load_class(defaults.PYBB_TOPIC_MOVE_VIEW)
TopicOpenView = load_class(defaults.PYBB_TOPIC_OPEN_VIEW)
TopicTrackerRedirectView = load_class(defaults.PYBB_TOPIC_TRACKER_REDIRECT_VIEW)
TopicPollVoteView = load_class(defaults.PYBB_TOPIC_POLL_VOTE_VIEW)
ModeratorListView = load_class(defaults.PYBB_MODERATOR_LIST_VIEW)
ModeratorDetailView = load_class(defaults.PYBB_MODERATOR_DETAIL_VIEW)
ModeratorCreateView = load_class(defaults.PYBB_MODERATOR_CREATE_VIEW)
ModeratorDeleteView = load_class(defaults.PYBB_MODERATOR_DELETE_VIEW)
UserPostsView = load_class(defaults.PYBB_USER_POSTS_VIEW)
UserPostsDeleteView = load_class(defaults.PYBB_USER_POSTS_DELETE_VIEW)
TopicsLatestView = load_class(defaults.PYBB_TOPICS_LATEST_VIEW)

SubscriptionListView = load_class(defaults.PYBB_SUBSCRIPTION_LIST_VIEW)
SubscriptionChangeView = load_class(defaults.PYBB_SUBSCRIPTION_CHANGE_VIEW)
SubscriptionDeleteView = load_class(defaults.PYBB_SUBSCRIPTION_DELETE_VIEW)

AttachmentListView = load_class(defaults.PYBB_ATTACHMENT_LIST_VIEW)
AttachmentDeleteView = load_class(defaults.PYBB_ATTACHMENT_DELETE_VIEW)

ForumMarkAsReadView = load_class(defaults.PYBB_FORUM_MARK_AS_READ_VIEW)


from pybb.views.base import (
    create_subscription,
    post_preview,
)
