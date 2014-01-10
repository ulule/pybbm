from pybb import defaults
from pybb.util import load_class

AttachmentForm = load_class(defaults.PYBB_ATTACHMENT_FORM)

PollAnswerForm = load_class(defaults.PYBB_POLL_ANSWER_FORM)

PollAnswerFormSet = load_class(defaults.PYBB_POLL_ANSWER_FORM_SET)

PostForm = load_class(defaults.PYBB_POST_FORM)

AdminPostForm = load_class(defaults.PYBB_ADMIN_POST_FORM)

AdminPostForm.__bases__ = (PostForm, )

UserSearchForm = load_class(defaults.PYBB_USER_SEARCH_FORM)

PollForm = load_class(defaults.PYBB_POLL_FORM)

ForumForm = load_class(defaults.PYBB_FORUM_FORM)

ModerationForm = load_class(defaults.PYBB_MODERATION_FORM)

SearchUserForm = load_class(defaults.PYBB_SEARCH_USER_FORM)

AttachmentFormSet = load_class(defaults.PYBB_ATTACHMENT_FORM_SET)

TopicMergeForm = load_class(defaults.PYBB_TOPIC_MERGE_FORM)

TopicMoveForm = load_class(defaults.PYBB_TOPIC_MOVE_FORM)

PostsMoveNewTopicForm = load_class(defaults.PYBB_POSTS_MOVE_NEW_TOPIC_FORM)

PostsMoveExistingTopicForm = load_class(defaults.PYBB_POSTS_MOVE_EXISTING_TOPIC_FORM)

from .base import (get_topic_merge_formset, get_topic_move_formset)  # NOQA
