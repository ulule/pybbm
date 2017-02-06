from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from pybb.models import Forum, Moderator
from pybb.models.base import get_moderator_ids_by_forum


@receiver(post_save, sender=Forum)
def clear_moderator_cache_forum_post_save(sender, instance, created, **kwargs):
    if created:
        get_moderator_ids_by_forum.cache_clear()


@receiver(post_delete, sender=Forum)
def clear_moderator_cache_forum_post_delete(sender, instance, using, **kwargs):
    get_moderator_ids_by_forum.cache_clear()


@receiver([post_save, post_delete], sender=Moderator)
def clear_moderator_cache_moderator_post_save_delete(sender, instance, **kwargs):
    get_moderator_ids_by_forum.cache_clear()

