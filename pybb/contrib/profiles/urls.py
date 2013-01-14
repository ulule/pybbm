from django.conf.urls import patterns, url

from pybb.contrib.profiles.views import ProfileUpdateView, UserDetailView


urlpatterns = patterns(
    '',
    # Profile
    url('^profile/edit/$',
        ProfileUpdateView.as_view(),
        name='profile_update'),
    url('^users/(?P<username>[^/]+)/$',
        UserDetailView.as_view(),
        name='user_detail'),
)
