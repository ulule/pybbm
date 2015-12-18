from django.conf.urls import url

from .views import (BanCreateView, BanListView,
                    BanDeleteView)


urlpatterns = [
    url('^ban/(?P<username>[^/]+)/create/$',
        BanCreateView.as_view(),
        name='ban_create'),

    url('^ban/(?P<username>[^/]+)/delete/$',
        BanDeleteView.as_view(),
        name='ban_delete'),

    url('^ban/list/$',
        BanListView.as_view(),
        name='ban_list'),
]
