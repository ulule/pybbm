from django.conf.urls import url

from .views import (ReportCreateView, ReportListView,
                    ReportDetailView, ReportCloseView)


urlpatterns = [
    url('^reports/(?P<pk>\d+)/create/$',
        ReportCreateView.as_view(),
        name='report_create'),
    url('^reports/(?P<pk>\d+)/detail/$',
        ReportDetailView.as_view(),
        name='report_detail'),
    url('^reports/(?P<pk>\d+)/close/$',
        ReportCloseView.as_view(),
        name='report_close'),
    url('^reports/list/$',
        ReportListView.as_view(),
        name='report_list'),
]
