from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^', include('pybb.urls', namespace='pybb')),
    (r'^', include('pybb.contrib.quotes.urls')),
    (r'^', include('pybb.contrib.profiles.urls')),
    (r'^', include('pybb.contrib.reports.urls')),
    (r'^', include('pybb.contrib.ban.urls')),
    (r'^accounts/', include('registration.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
