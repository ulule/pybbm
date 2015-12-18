from django.conf.urls import url

from .views import QuoteView


urlpatterns = [
    url('^post/quote/$',
        QuoteView.as_view(),
        name='quote'),
]
