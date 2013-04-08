from django.conf.urls import patterns, url

from haystack.views import search_view_factory

from pybb.contrib.search.views import SearchView
from pybb.contrib.search.forms import SearchForm
from pybb.contrib.search.settings import PYBB_SEARCH_SEARCH_URL


urlpatterns = patterns(
    '',
    url(PYBB_SEARCH_SEARCH_URL,
        search_view_factory(
            view_class=SearchView,
            template='pybb/search.html',
            form_class=SearchForm,
        ),
        name='search'),
)
