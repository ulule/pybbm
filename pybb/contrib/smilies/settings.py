from django.conf import settings

PYBB_SMILIES_PREFIX = getattr(settings, 'PYBB_SMILIES_PREFIX', 'pybb/smilies/')

PYBB_SMILIES_STYLE_CLASS = getattr(settings, 'PYBB_SMILIES_STYLE_CLASS', 'smiley')

PYBB_SMILIES_USE_CACHE = getattr(settings, 'PYBB_SMILIES_USE_CACHE', True)
