# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Permission
from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.db.models.signals import post_save

from pybb import defaults


def user_saved(instance, created, **kwargs):
    if not created:
        return
    try:
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'pybb', 'post')
        add_topic_permission = Permission.objects.get_by_natural_key('add_topic', 'pybb', 'topic')
    except ObjectDoesNotExist:
        return
    instance.user_permissions.add(add_post_permission, add_topic_permission)
    instance.save()
    if settings.AUTH_PROFILE_MODULE == 'pybb.Profile':
        from pybb.contrib.profiles.models import Profile
        Profile(user=instance).save()


def setup_signals():
    if defaults.PYBB_AUTO_USER_PERMISSIONS:
        post_save.connect(user_saved, sender=User)
