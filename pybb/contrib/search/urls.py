from django.conf.urls import patterns, url

from haystack.views import search_view_factory

from .views import SearchView
from .forms import SearchForm
from .settings import PYBB_SEARCH_SEARCH_URL


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
