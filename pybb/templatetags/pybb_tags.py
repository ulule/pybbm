# -*- coding: utf-8 -*-
import math
import time

from django import template
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat


try:
    import pytils
    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from pybb.models import TopicReadTracker, ForumReadTracker, PollAnswerUser
from pybb import defaults
from pybb.util import tznow, timedelta, load_class

register = template.Library()


#noinspection PyUnusedLocal
@register.tag
def pybb_time(parser, token):
    try:
        tag, context_time = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('pybb_time requires single argument')
    else:
        return PybbTimeNode(context_time)


class PybbTimeNode(template.Node):
    def __init__(self, time):
        self.time = template.Variable(time)

    def render(self, context):
        context_time = self.time.resolve(context)

        delta = tznow() - context_time
        today = tznow().replace(hour=0, minute=0, second=0)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        if delta.days == 0:
            if delta.seconds < 60:
                if context['LANGUAGE_CODE'].startswith('ru') and pytils_enabled:
                    msg = _('seconds ago,seconds ago,seconds ago')
                    msg = pytils.numeral.choose_plural(delta.seconds, msg)
                else:
                    msg = _('seconds ago')
                return u'%d %s' % (delta.seconds, msg)

            elif delta.seconds < 3600:
                minutes = int(delta.seconds / 60)
                if context['LANGUAGE_CODE'].startswith('ru') and pytils_enabled:
                    msg = _('minutes ago,minutes ago,minutes ago')
                    msg = pytils.numeral.choose_plural(minutes, msg)
                else:
                    msg = _('minutes ago')
                return u'%d %s' % (minutes, msg)
        if context['user'].is_authenticated():
            if time.daylight:
                tz1 = time.altzone
            else:
                tz1 = time.timezone

            default_tz = load_class(defaults.PYBB_TIMEZONE_FROM_USER)(context['user'])

            tz = tz1 + default_tz * 60 * 60
            context_time = context_time + timedelta(seconds=tz)
        if today < context_time < tomorrow:
            return _('today, %s') % context_time.strftime('%H:%M')

        if yesterday < context_time < today:
            return _('yesterday, %s') % context_time.strftime('%H:%M')

        return dateformat.format(context_time, 'd M, Y H:i')


@register.filter
def pybb_post_anchor_url(post, user):
    return post.get_anchor_url(user)


@register.simple_tag
def pybb_link(object, anchor=u''):
    """
    Return A tag with link to object.
    """

    url = hasattr(object, 'get_absolute_url') and object.get_absolute_url() or None
    #noinspection PyRedeclaration
    anchor = anchor or smart_unicode(object)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))


@register.filter
def pybb_topic_moderated_by(topic, user):
    """
    Check if user is moderator of topic's forum.
    """

    return pybb_forum_moderated_by(topic.forum, user)


@register.filter
def pybb_forum_moderated_by(forum, user):
    """
    Check if user is moderator of forum.
    """

    return forum.is_moderated_by(user)


@register.filter
def pybb_editable_by(post, user):
    """
    Check if the post could be edited by the user.
    """

    return post.is_editable_by(user)


@register.filter
def pybb_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """
    return post.is_posted_by(user)


@register.filter
def pybb_topic_unread(topics, user):
    """
    Mark all topics in queryset/list with .unread for target user
    """
    topic_list = list(topics)

    forum_marks = {}

    if user.is_authenticated():
        for topic in topic_list:
            topic.unread = True

            if not topic.forum_id in forum_marks:
                try:
                    forum_mark = ForumReadTracker.objects.get(user=user, forum=topic.forum_id)
                except:
                    forum_mark = None

                forum_marks[topic.forum_id] = forum_mark

        qs = TopicReadTracker.objects.filter(
            user=user,
            topic__in=topic_list
        ).select_related('topic')

        if forum_marks:
            for topic in topic_list:
                if not topic.forum_id in forum_marks or not forum_marks[topic.forum_id]:
                    continue

                forum_mark = forum_marks[topic.forum_id]

                if topic.updated and (topic.updated <= forum_mark.time_stamp):
                    topic.unread = False

        topic_marks = list(qs)
        topic_dict = dict(((topic.id, topic) for topic in topic_list))

        for mark in topic_marks:
            if ((topic_dict[mark.topic.id].updated is None) or
               (topic_dict[mark.topic.id].updated <= mark.time_stamp)):
                topic_dict[mark.topic.id].unread = False

    return topic_list


@register.filter
def pybb_forum_unread(forums, user):
    """
    Check if forum has unread messages.
    """
    forum_list = list(forums)
    if user.is_authenticated():
        for forum in forum_list:
            if forum.topic_count:
                forum.unread = True
        forum_marks = ForumReadTracker.objects.filter(
            user=user,
            forum__in=forum_list
        ).select_related('forum')
        forum_dict = dict(((forum.id, forum) for forum in forum_list))
        for mark in forum_marks:
            if ((forum_dict[mark.forum.id].updated is None) or
               (forum_dict[mark.forum.id].updated <= mark.time_stamp)):
                forum_dict[mark.forum.id].unread = False
    return forum_list


@register.filter
def pybb_topic_inline_pagination(topic):
    page_count = int(math.ceil(topic.post_count / float(defaults.PYBB_TOPIC_PAGE_SIZE)))

    if page_count <= 5:
        return range(1, page_count + 1)

    return range(1, 5) + ['...', page_count]


@register.filter
def pybb_topic_poll_not_voted(poll, user):
    return not PollAnswerUser.objects.filter(poll_answer__poll=poll, user=user).exists()


@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)


class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''
