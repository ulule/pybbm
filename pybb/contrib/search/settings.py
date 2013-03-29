from django.conf import settings

PYBB_SEARCH_SEARCH_VIEW = getattr(settings,
                                  'PYBB_SEARCH_SEARCH_VIEW',
                                  'pybb.contrib.search.views.base.SearchView')

PYBB_SEARCH_SEARCH_FORM = getattr(settings,
                                  'PYBB_SEARCH_SEARCH_FORM',
                                  'pybb.contrib.search.forms.base.SearchForm')
