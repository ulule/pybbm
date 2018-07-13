from django.conf.urls import include, url
from django.contrib import admin


admin.autodiscover()

urlpatterns = [
    url(r'^', include('pybb.urls', namespace='pybb')),
    url(r'^', include('pybb.contrib.quotes.urls')),
    url(r'^', include('pybb.contrib.profiles.urls')),
    url(r'^', include('pybb.contrib.reports.urls')),
    url(r'^', include('pybb.contrib.ban.urls')),
    url(r'^admin/', include(admin.site.urls[:2])),
]
