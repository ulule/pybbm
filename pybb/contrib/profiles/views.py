from django.views import generic
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from pybb.models import Topic
from pybb.compat import get_user_model

from .forms import EditProfileForm


class ProfileUpdateView(generic.UpdateView):
    template_name = 'pybb/profile_update.html'
    form_class = EditProfileForm

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(ProfileUpdateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('profile_update')


class UserDetailView(generic.DetailView):
    template_name = 'pybb/user/detail.html'
    context_object_name = 'target_user'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, username=self.kwargs['username'])

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_context_data(self, **kwargs):
        ctx = super(UserDetailView, self).get_context_data(**kwargs)
        ctx['topic_count'] = Topic.objects.filter(user=ctx['target_user']).count()
        return ctx
