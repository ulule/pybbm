from django.db import models

from pybb.base import ModelBase, ManagerBase
from pybb.contrib.smilies import settings


class SmileyManager(ManagerBase):
    def active(self):
        "Retrieves active smilies"
        return self.get_query_set().filter(is_active=True)

    def one_click(self):
        "Retrieves smilies that are both active and 'in one click'"
        return self.active().filter(in_one_click=True)

    def has_more(self):
        "Returns true if there is active smilies not 'in one click'"
        return self.active().filter(in_one_click=False).exists()

    def for_matching(self):
        "Retrieves active smilies in matching order"
        return self.active().order_by('match_order', 'pk')


class Smiley(ModelBase):
    pattern = models.CharField(max_length=25)
    title = models.CharField(max_length=25, blank=True)
    image = models.ImageField(upload_to=settings.PYBB_SMILIES_PREFIX)
    is_active = models.BooleanField(default=True, db_index=True)
    in_one_click = models.BooleanField(default=False, db_index=True)
    display_order = models.PositiveIntegerField(default=100, db_index=True)
    match_order = models.PositiveIntegerField(default=100, db_index=True)

    objects = SmileyManager()

    def __unicode__(self):
        return self.title or self.pattern

    class Meta:
        app_label = 'pybb'
        ordering = ['display_order', 'pk']
