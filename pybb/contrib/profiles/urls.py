from django.conf.urls import url

from .views import ProfileUpdateView, UserDetailView


urlpatterns = [
    # Profile
    url('^profile/edit/$',
        ProfileUpdateView.as_view(),
        name='profile_update'),
    url('^users/(?P<username>[^/]+)/$',
        UserDetailView.as_view(),
        name='user_detail'),
]
