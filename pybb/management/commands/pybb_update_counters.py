#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import unicode_literals
from itertools import chain

from django.core.management.base import BaseCommand

from pybb.models import Topic, Forum
from pybb.models.mixins import prefetch_parent_forums


class Command(BaseCommand):
    help = 'Recalc post counters for forums and topics'

    def add_arguments(self, parser):
        parser.add_argument('--no-topics',
                            action='store_true',
                            dest='no_topics',
                            default=False,
                            help='Do not update counters for topics'),

    def handle(self, *args, **options):
        no_topics = options.get('no_topics')

        if not no_topics:
            for topic in Topic.objects.all():
                topic.update_counters(update_forum=False)
                self.stdout.write('Successfully updated topic "%s"\n' % topic)

        forums = list(Forum.objects.all())
        prefetch_parent_forums(forums, forum_cache_by_id={forum.id: forum for forum in forums})
        parent_forums = set(chain(*(forum.forum_ids for forum in forums)))
        forums_to_update = [forum for forum in forums if forum.id not in parent_forums]

        for forum in forums_to_update:
            forum.update_counters()
            self.stdout.write('Successfully updated forum "%s"\n' % forum)
