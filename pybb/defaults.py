# -*- coding: utf-8 -*-
import os.path

from django.conf import settings
from django.core.urlresolvers import reverse


PYBB_TOPIC_PAGE_SIZE = getattr(settings, 'PYBB_TOPIC_PAGE_SIZE', 10)
PYBB_FORUM_PAGE_SIZE = getattr(settings, 'PYBB_FORUM_PAGE_SIZE', 20)
PYBB_AVATAR_WIDTH = getattr(settings, 'PYBB_AVATAR_WIDTH', 80)
PYBB_AVATAR_HEIGHT = getattr(settings, 'PYBB_AVATAR_HEIGHT', 80)
PYBB_MAX_AVATAR_SIZE = getattr(settings, 'PYBB_MAX_AVATAR_SIZE', 1024 * 50)
PYBB_DEFAULT_TIME_ZONE = getattr(settings, 'PYBB_DEFAULT_TIME_ZONE', 3)

PYBB_SIGNATURE_MAX_LENGTH = getattr(settings, 'PYBB_SIGNATURE_MAX_LENGTH', 1024)
PYBB_SIGNATURE_MAX_LINES = getattr(settings, 'PYBB_SIGNATURE_MAX_LINES', 3)

PYBB_FREEZE_FIRST_POST = getattr(settings, 'PYBB_FREEZE_FIRST_POST', False)

PYBB_ATTACHMENT_SIZE_LIMIT = getattr(settings, 'PYBB_ATTACHMENT_SIZE_LIMIT', 1024 * 1024)
PYBB_ATTACHMENT_ENABLE = getattr(settings, 'PYBB_ATTACHMENT_ENABLE', True)
PYBB_NOTIFICATION_ENABLE = getattr(settings, 'PYBB_NOTIFICATION_ENABLE', False)
PYBB_ATTACHMENT_UPLOAD_TO = getattr(settings, 'PYBB_ATTACHMENT_UPLOAD_TO', os.path.join('pybb', 'attachments'))
PYBB_ATTACHMENT_BASE_URL = getattr(settings, 'PYBB_ATTACHMENT_BASE_URL', os.path.join(settings.MEDIA_URL, 'pybb', 'attachments/'))
PYBB_ATTACHMENT_LOCATION = getattr(settings, 'PYBB_ATTACHMENT_LOCATION', os.path.join(settings.MEDIA_ROOT,
                                                                                      PYBB_ATTACHMENT_UPLOAD_TO))

PYBB_DEFAULT_AVATAR_URL = getattr(settings, 'PYBB_DEFAULT_AVATAR_URL',
                                  getattr(settings, 'STATIC_URL', '') + 'pybb/img/default_avatar.jpg')

PYBB_DEFAULT_TITLE = getattr(settings, 'PYBB_DEFAULT_TITLE', 'PYBB Powered Forum')

PYBB_MARKUP_PREPROCESSORS = getattr(settings, 'PYBB_MARKUP_PREPROCESSORS', (
    'pybb.contrib.quotes.processors.QuotePreProcessor',
    'pybb.contrib.smilies.processors.SmileyProcessor',
))
PYBB_MARKUP_POSTPROCESSORS = getattr(settings, 'PYBB_MARKUP_POSTPROCESSORS', (
))

PYBB_MARKUP = getattr(settings, 'PYBB_MARKUP', 'bbcode')
PYBB_MARKUP_ENGINE = getattr(settings, 'PYBB_MARKUP_ENGINE', 'pybb.engines.bbcode.BBCodeMarkupEngine')

PYBB_BBCODE_MARKUP_SIMPLE_FORMATTERS = getattr(settings, 'PYBB_BBCODE_MARKUP_SIMPLE_FORMATTERS', ())
PYBB_BBCODE_MARKUP_FORMATTERS = getattr(settings, 'PYBB_BBCODE_MARKUP_FORMATTERS', ())


PYBB_QUOTE_ENGINE = getattr(settings, 'PYBB_QUOTE_ENGINE', 'pybb.engines.bbcode.BBCodeQuoteEngine')

PYBB_BUTTONS = getattr(settings, 'PYBB_BUTTONS', {})

PYBB_TEMPLATE = getattr(settings, 'PYBB_TEMPLATE', "base.html")
PYBB_DEFAULT_AUTOSUBSCRIBE = getattr(settings, 'PYBB_DEFAULT_AUTOSUBSCRIBE', True)
PYBB_ENABLE_ANONYMOUS_POST = getattr(settings, 'PYBB_ENABLE_ANONYMOUS_POST', False)
PYBB_ANONYMOUS_USERNAME = getattr(settings, 'PYBB_ANONYMOUS_USERNAME', 'Anonymous')
PYBB_PREMODERATION = getattr(settings, 'PYBB_PREMODERATION', False)

PYBB_BODY_CLEANERS = getattr(settings, 'PYBB_BODY_CLEANERS', ['pybb.util.rstrip_str', ])

PYBB_BODY_VALIDATOR = getattr(settings, 'PYBB_BODY_VALIDATOR', None)

PYBB_POLL_MAX_ANSWERS = getattr(settings, 'PYBB_POLL_MAX_ANSWERS', 10)

PYBB_AUTO_USER_PERMISSIONS = getattr(settings, 'PYBB_AUTO_USER_PERMISSIONS', False)

PYBB_DUPLICATE_TOPIC_SLUG_ALLOWED = getattr(settings, 'PYBB_DUPLICATE_TOPIC_SLUG_ALLOWED', True)

PYBB_FORUM_PERMISSIONS = (
    'can_stick_topic',
    'can_unstick_topic',
    'can_open_topic',
    'can_close_topic',
    'can_merge_topic',
    'can_change_topic',
    'can_move_topic',
    'can_move_post',
    'can_change_poll',
    'can_publish_announce',
    'can_change_post',
    'can_delete_post',
    'can_see_user_ip',
    'can_change_attachment',
)

PYBB_USER_PERMISSIONS = (
    'can_define_password',
    'can_ban_user',
    'can_unban_user',
    'can_change_signature',
    'can_change_avatar',
)

PYBB_ATTACHMENT_FORM = getattr(settings, 'PYBB_ATTACHMENT_FORM', 'pybb.forms.base.AttachmentForm')
PYBB_POLL_ANSWER_FORM = getattr(settings, 'PYBB_POLL_ANSWER_FORM', 'pybb.forms.base.PollAnswerForm')
PYBB_POLL_ANSWER_FORM_SET = getattr(settings, 'PYBB_POLL_ANSWER_FORM_SET', 'pybb.forms.base.PollAnswerFormSet')
PYBB_POST_FORM = getattr(settings, 'PYBB_POST_FORM', 'pybb.forms.base.PostForm')
PYBB_ADMIN_POST_FORM = getattr(settings, 'PYBB_ADMIN_POST_FORM', 'pybb.forms.base.AdminPostForm')
PYBB_USER_SEARCH_FORM = getattr(settings, 'PYBB_USER_SEARCH_FORM', 'pybb.forms.base.UserSearchForm')
PYBB_POLL_FORM = getattr(settings, 'PYBB_POLL_FORM', 'pybb.forms.base.PollForm')
PYBB_TOPIC_MERGE_FORM = getattr(settings, 'PYBB_TOPIC_MERGE_FORM', 'pybb.forms.base.TopicMergeForm')
PYBB_TOPIC_MOVE_FORM = getattr(settings, 'PYBB_TOPIC_MOVE_FORM', 'pybb.forms.base.TopicMoveForm')
PYBB_FORUM_FORM = getattr(settings, 'PYBB_FORUM_FORM', 'pybb.forms.base.ForumForm')
PYBB_MODERATION_FORM = getattr(settings, 'PYBB_MODERATION_FORM', 'pybb.forms.base.ModerationForm')
PYBB_SEARCH_USER_FORM = getattr(settings, 'PYBB_SEARCH_USER_FORM', 'pybb.forms.base.SearchUserForm')
PYBB_POSTS_MOVE_NEW_TOPIC_FORM = getattr(settings, 'PYBB_POSTS_MOVE_NEW_TOPIC_FORM', 'pybb.forms.base.PostsMoveNewTopicForm')
PYBB_POSTS_MOVE_EXISTING_TOPIC_FORM = getattr(settings, 'PYBB_POSTS_MOVE_EXISTING_TOPIC_FORM', 'pybb.forms.base.PostsMoveExistingTopicForm')
PYBB_ATTACHMENT_FORM_SET = getattr(settings, 'PYBB_ATTACHMENT_FORM_SET', 'pybb.forms.base.AttachmentFormSet')

PYBB_QUOTES_USER_URL = getattr(settings, 'PYBB_QUOTES_USER_URL',
                               lambda user: reverse('user_detail', args=[user.username]))

PYBB_INDEX_VIEW = getattr(settings, 'PYBB_INDEX_VIEW', 'pybb.views.base.IndexView')

PYBB_FORUM_CREATE_VIEW = getattr(settings, 'PYBB_FORUM_CREATE_VIEW', 'pybb.views.base.ForumCreateView')
PYBB_FORUM_DETAIL_VIEW = getattr(settings, 'PYBB_FORUM_DETAIL_VIEW', 'pybb.views.base.ForumDetailView')
PYBB_FORUM_UPDATE_VIEW = getattr(settings, 'PYBB_FORUM_UPDATE_VIEW', 'pybb.views.base.ForumUpdateView')

PYBB_TOPIC_DETAIL_VIEW = getattr(settings, 'PYBB_TOPIC_DETAIL_VIEW', 'pybb.views.base.TopicDetailView')
PYBB_TOPIC_DELETE_VIEW = getattr(settings, 'PYBB_TOPIC_DELETE_VIEW', 'pybb.views.base.TopicDeleteView')
PYBB_TOPIC_STICK_VIEW = getattr(settings, 'PYBB_TOPIC_STICK_VIEW', 'pybb.views.base.TopicStickView')
PYBB_TOPIC_UNSTICK_VIEW = getattr(settings, 'PYBB_TOPIC_UNSTICK_VIEW', 'pybb.views.base.TopicUnstickView')
PYBB_TOPIC_CLOSE_VIEW = getattr(settings, 'PYBB_TOPIC_CLOSE_VIEW', 'pybb.views.base.TopicCloseView')
PYBB_TOPIC_MERGE_VIEW = getattr(settings, 'PYBB_TOPIC_MERGE_VIEW', 'pybb.views.base.TopicMergeView')
PYBB_TOPIC_MOVE_VIEW = getattr(settings, 'PYBB_TOPIC_MOVE_VIEW', 'pybb.views.base.TopicMoveView')
PYBB_TOPIC_OPEN_VIEW = getattr(settings, 'PYBB_TOPIC_OPEN_VIEW', 'pybb.views.base.TopicOpenView')
PYBB_TOPIC_POLL_VOTE_VIEW = getattr(settings, 'PYBB_TOPIC_POLL_VOTE_VIEW', 'pybb.views.base.TopicPollVoteView')
PYBB_TOPIC_TRACKER_REDIRECT_VIEW = getattr(settings, 'PYBB_TOPIC_TRACKER_REDIRECT_VIEW', 'pybb.views.base.TopicTrackerRedirectView')

PYBB_POSTS_MOVE_VIEW = getattr(settings, 'PYBB_POSTS_MOVE_VIEW', 'pybb.views.base.PostsMoveView')
PYBB_POST_CREATE_VIEW = getattr(settings, 'PYBB_POST_CREATE_VIEW', 'pybb.views.base.PostCreateView')
PYBB_POSTS_CREATE_VIEW = getattr(settings, 'PYBB_POSTS_CREATE_VIEW', 'pybb.views.base.PostsCreateView')
PYBB_POST_UPDATE_VIEW = getattr(settings, 'PYBB_POST_UPDATE_VIEW', 'pybb.views.base.PostUpdateView')
PYBB_POST_REDIRECT_VIEW = getattr(settings, 'PYBB_POST_REDIRECT_VIEW', 'pybb.views.base.PostRedirectView')
PYBB_POST_MODERATE_VIEW = getattr(settings, 'PYBB_POST_MODERATE_VIEW', 'pybb.views.base.PostModerateView')
PYBB_POST_DELETE_VIEW = getattr(settings, 'PYBB_POST_DELETE_VIEW', 'pybb.views.base.PostDeleteView')

PYBB_USER_POSTS_VIEW = getattr(settings, 'PYBB_USER_POSTS_VIEW', 'pybb.views.base.UserPostsView')
PYBB_USER_POSTS_DELETE_VIEW = getattr(settings, 'PYBB_USER_POSTS_DELETE_VIEW', 'pybb.views.base.UserPostsDeleteView')
PYBB_TOPICS_LATEST_VIEW = getattr(settings, 'PYBB_TOPICS_LATEST_VIEW', 'pybb.views.base.TopicsLatestView')

PYBB_SUBSCRIPTION_LIST_VIEW = getattr(settings, 'PYBB_SUBSCRIPTION_LIST_VIEW', 'pybb.views.base.SubscriptionListView')
PYBB_SUBSCRIPTION_CHANGE_VIEW = getattr(settings, 'PYBB_SUBSCRIPTION_CHANGE_VIEW', 'pybb.views.base.SubscriptionChangeView')
PYBB_SUBSCRIPTION_DELETE_VIEW = getattr(settings, 'PYBB_SUBSCRIPTION_DELETE_VIEW', 'pybb.views.base.SubscriptionDeleteView')

PYBB_MODERATOR_LIST_VIEW = getattr(settings, 'PYBB_MODERATOR_LIST_VIEW', 'pybb.views.base.ModeratorListView')
PYBB_MODERATOR_DETAIL_VIEW = getattr(settings, 'PYBB_MODERATOR_DETAIL_VIEW', 'pybb.views.base.ModeratorDetailView')
PYBB_MODERATOR_CREATE_VIEW = getattr(settings, 'PYBB_MODERATOR_CREATE_VIEW', 'pybb.views.base.ModeratorCreateView')
PYBB_MODERATOR_DELETE_VIEW = getattr(settings, 'PYBB_MODERATOR_DELETE_VIEW', 'pybb.views.base.ModeratorDeleteView')
PYBB_LOG_MODERATION_VIEW = getattr(settings, 'PYBB_LOG_MODERATION_VIEW', 'pybb.views.base.LogModerationListView')

PYBB_ATTACHMENT_LIST_VIEW = getattr(settings, 'PYBB_ATTACHMENT_LIST_VIEW', 'pybb.views.base.AttachmentListView')
PYBB_ATTACHMENT_DELETE_VIEW = getattr(settings, 'PYBB_ATTACHMENT_DELETE_VIEW', 'pybb.views.base.AttachmentDeleteView')

PYBB_FORUM_MARK_AS_READ_VIEW = getattr(settings, 'PYBB_FORUM_MARK_AS_READ_VIEW', 'pybb.views.base.ForumMarkAsReadView')

PYBB_SUBSCRIPTION_MODEL = getattr(settings, 'PYBB_SUBSCRIPTION_MODEL', 'pybb.models.subscription.Subscription')
PYBB_POLL_MODEL = getattr(settings, 'PYBB_POLL_MODEL', 'pybb.models.poll.Poll')
PYBB_MODERATOR_MODEL = getattr(settings, 'PYBB_MODERATOR_MODEL', 'pybb.models.moderation.Moderator')
PYBB_FORUM_MODEL = getattr(settings, 'PYBB_FORUM_MODEL', 'pybb.models.forum.Forum')
PYBB_TOPIC_MODEL = getattr(settings, 'PYBB_TOPIC_MODEL', 'pybb.models.topic.Topic')
PYBB_POST_MODEL = getattr(settings, 'PYBB_POST_MODEL', 'pybb.models.post.Post')
PYBB_ATTACHMENT_MODEL = getattr(settings, 'PYBB_ATTACHMENT_MODEL', 'pybb.models.attachment.Attachment')
PYBB_TOPIC_READ_TRACKER_MODEL = getattr(settings, 'PYBB_TOPIC_READ_TRACKER_MODEL', 'pybb.models.tracker.TopicReadTracker')
PYBB_FORUM_READ_TRACKER_MODEL = getattr(settings, 'PYBB_FORUM_READ_TRACKER_MODEL', 'pybb.models.tracker.ForumReadTracker')
PYBB_POLL_ANSWER_MODEL = getattr(settings, 'PYBB_POLL_ANSWER_MODEL', 'pybb.models.poll.PollAnswer')
PYBB_POLL_ANSWER_USER_MODEL = getattr(settings, 'PYBB_POLL_ANSWER_USER_MODEL', 'pybb.models.poll.PollAnswerUser')
PYBB_LOG_MODERATION_MODEL = getattr(settings, 'PYBB_LOG_MODERATION_MODEL', 'pybb.models.moderation.LogModeration')

PYBB_PRE_POST_CREATE_FILTERS = getattr(settings, 'PYBB_PRE_POST_CREATE_FILTERS', (
    'pybb.filters.PrePostCreateFilter',
))

PYBB_UPDATE_MENTION_POST_DELTA = getattr(settings, 'PYBB_UPDATE_MENTION_POST_DELTA', 180)
