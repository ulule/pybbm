from pybb import defaults
from pybb.util import load_class

from pybb.models.base import BaseTopicRedirection, UserObjectPermission, PostDeletion  # NOQA


class TopicRedirection(BaseTopicRedirection):
    class Meta(BaseTopicRedirection.Meta):
        abstract = False


Moderator = load_class(defaults.PYBB_MODERATOR_MODEL)
Forum = load_class(defaults.PYBB_FORUM_MODEL)
Post = load_class(defaults.PYBB_POST_MODEL)
Topic = load_class(defaults.PYBB_TOPIC_MODEL)
TopicReadTracker = load_class(defaults.PYBB_TOPIC_READ_TRACKER_MODEL)
ForumReadTracker = load_class(defaults.PYBB_FORUM_READ_TRACKER_MODEL)
PollAnswer = load_class(defaults.PYBB_POLL_ANSWER_MODEL)
PollAnswerUser = load_class(defaults.PYBB_POLL_ANSWER_USER_MODEL)
LogModeration = load_class(defaults.PYBB_LOG_MODERATION_MODEL)
Attachment = load_class(defaults.PYBB_ATTACHMENT_MODEL)
Poll = load_class(defaults.PYBB_POLL_MODEL)
Subscription = load_class(defaults.PYBB_SUBSCRIPTION_MODEL)


Forum.on_change(Forum.watch_forum)

Post.on_change(Post.watch_topic)
