from django.conf.urls import patterns, url

from haystack.views import search_view_factory

from pybb.contrib.search.views import SearchView
from pybb.contrib.search.forms import SearchForm


urlpatterns = patterns(
    '',
    url(r'^search/',
        search_view_factory(
            view_class=SearchView,
            template='forum/search.html',
            form_class=SearchForm,
        ),
        name='search'),
)
