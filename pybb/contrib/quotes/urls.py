from django.conf.urls import url, patterns

from .views import QuoteView


urlpatterns = patterns(
    '',
    url('^post/quote/$',
        QuoteView.as_view(),
        name='quote'),
)
