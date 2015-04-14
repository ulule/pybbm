from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.views.generic.edit import FormMixin
from django.core.urlresolvers import reverse

from pybb.util import generic
from pybb import defaults
from pybb.compat import get_user_model

from .forms import BanForm
from .models import BannedUser, IPAddress

from pure_pagination.paginator import Paginator


class BanCreateView(generic.DetailView, FormMixin):
    slug_url_kwarg = 'username'
    slug_field = 'username'
    form_class = BanForm
    template_name = 'pybb/ban/create.html'

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_form_kwargs(self, **kwargs):
        return dict(super(BanCreateView, self).get_form_kwargs(**kwargs), **{
            'user': self.object
        })

    def get_context_data(self, **kwargs):
        data = super(BanCreateView, self).get_context_data(**kwargs)

        return dict(data, **{
            'form': self.get_form(self.get_form_class()),
        })

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data(object=self.object)

        form = context['form']

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('ban_list')

    def form_valid(self, form):
        banned, banned_ips = form.save()

        return redirect(self.get_success_url())

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BanCreateView, self).dispatch(request, *args, **kwargs)


class BanListView(generic.ListView):
    model = BannedUser
    template_name = 'pybb/ban/list.html'
    context_object_name = 'banned_list'
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    paginator_class = Paginator

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BanListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related('user')


class BanDeleteView(generic.DeleteView):
    template_name = 'pybb/ban/delete.html'
    slug_url_kwarg = 'username'
    slug_field = 'user__username'
    model = BannedUser
    context_object_name = 'banned'

    def get_context_data(self, **kwargs):
        return dict(super(BanDeleteView, self).get_context_data(**kwargs), **{
            'ip_addresses': IPAddress.objects.filter(user=self.object.user, banned=True)
        })

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BanDeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        response = super(BanDeleteView, self).delete(request, *args, **kwargs)

        BannedUser.objects.filter(user=self.object.user).delete()

        IPAddress.objects.filter(user=self.object.user).update(banned=False)

        return response

    def get_success_url(self):
        return reverse('ban_list')
