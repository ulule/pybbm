from django.views.generic.edit import FormMixin
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from .models import ReportMessage, Report
from .forms import ReportMessageForm
from pybb.models import Post

from pure_pagination.paginator import Paginator


class ReportCreateView(generic.DetailView, FormMixin):
    model = Post
    template_name = 'pybb/report/create.html'
    form_class = ReportMessageForm
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.is_reportable(self.object):
            return self.already_reported()

        context = self.get_context_data(object=self.object)

        return self.render_to_response(context)

    def already_reported(self):
        messages.error(self.request, _('You have already reported this post on %(topic)s!') % {
            'topic': self.object.topic
        })

        return redirect(self.get_success_url())

    def is_reportable(self, post):
        return (ReportMessage.objects.filter(user=self.request.user,
                                             report__post=post).count()) == 0

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.is_reportable(self.object):
            return self.already_reported()

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        data = super(ReportCreateView, self).get_context_data(**kwargs)

        return dict(data, **{
            'form': self.get_form(self.get_form_class()),
        })

    def get_form_kwargs(self):
        return dict(super(ReportCreateView, self).get_form_kwargs(), **{
            'user': self.request.user,
            'post': self.object
        })

    def form_valid(self, form):
        self.report_message = form.save()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.object.topic.get_absolute_url()

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ReportCreateView, self).dispatch(request, *args, **kwargs)


class ReportListView(generic.ListView):
    model = Report
    template_name = 'pybb/report/list.html'
    context_object_name = 'report_list'
    paginator_class = Paginator

    def get_queryset(self):
        return self.model.objects.order_by('-updated').select_related('post', 'post__topic')

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ReportListView, self).dispatch(request, *args, **kwargs)


class ReportDetailView(generic.DetailView):
    model = Report
    template_name = 'pybb/report/detail.html'
    context_object_name = 'report'

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ReportDetailView, self).dispatch(request, *args, **kwargs)


class ReportCloseView(generic.DetailView):
    model = Report
    context_object_name = 'report'

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ReportCloseView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.close()

        self.get_context_data(object=self.object)

        return redirect(reverse('report_list'))
