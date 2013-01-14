# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mass_mail
from django import forms

from pybb.util import tznow

email_validator = forms.EmailField()


def notify_topic_subscribers(post):
    from pybb.models import Subscription

    topic = post.topic
    if post == topic.head:
        return

    subscriptions = (Subscription.objects.filter(topic=topic,
                                                 type=Subscription.TYPE_INSTANT_ALERT,
                                                 sent=False)
                     .exclude(user=post.user)
                     .select_related('user'))

    params = {
        'post_url': post.get_absolute_url(),
        'post': post,
        'sender': post.user,
        'topic': topic,
        'topic_url': topic.get_absolute_url(),
        'forum': topic.forum,
        'forum_url': topic.forum.get_absolute_url()
    }

    messages = []

    for subscription in subscriptions:
        user = subscription.user

        try:
            email_validator.clean(user.email)
        except Exception as e:
            logging.error(e)
            continue

        subject = render_to_string('pybb/mails/subscription_email_subject.html',
                                   dict(params, **{
                                       'user': user
                                   }))
        message = render_to_string('pybb/mails/subscription_email_body.html',
                                   dict(params, **{
                                       'user': user
                                   }))
        messages.append((''.join(subject.splitlines()), message, settings.DEFAULT_FROM_EMAIL, [user.email]))

    if messages:
        result = send_mass_mail(messages, fail_silently=True)

        subscriptions.update(sent=True, updated=tznow())

        return result

    return False
