from django.contrib import admin

from .models import Smiley


class SmileyAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'title', 'image', 'is_active', 'in_one_click', 'display_order', 'match_order')
    list_filter = ('is_active', 'in_one_click')
    search_fields = ('pattern', 'title', 'image')

admin.site.register(Smiley, SmileyAdmin)
