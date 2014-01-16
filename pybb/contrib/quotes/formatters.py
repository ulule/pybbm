# -*- coding: utf-8 -*-
from pybb.compat import User
from pybb.models import Post

from .signals import quoted
from . import settings


def quote(tag_name, value, options, parent, context):
    if not 'quote' in options:
        return value

    splits = options['quote'].split(';')

    try:
        username, post_id = splits

        post_id = int(post_id)
    except ValueError:
        if len(splits) == 1:
            return settings.PYBB_QUOTES_QUOTE_MINIMAL_FORMAT % {
                'message': value,
                'username': splits[0],
            }

        return settings.PYBB_QUOTES_QUOTE_BASIC_FORMAT % {
            'message': value,
        }

    try:
        post = Post.objects.get(pk=post_id)
        user = post.user
    except (Post.DoesNotExist, User.DoesNotExist):
        return settings.PYBB_QUOTES_QUOTE_MINIMAL_FORMAT % {
            'message': value,
            'username': splits[0],
        }

    if 'obj' in context and context['obj']:
        current_post = context['obj']

        if current_post.user:
            quoted.send(sender=current_post.__class__,
                        user=current_post.user,
                        from_post=current_post,
                        to_post=post)

    return settings.PYBB_QUOTES_QUOTE_VALID_FORMAT % {
        'user_url': settings.PYBB_QUOTES_USER_URL(user),
        'message': value,
        'username': username,
        'post_url': settings.PYBB_QUOTES_POST_URL(post)  # anonymous anchor url
    }
