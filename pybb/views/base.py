# -*- coding: utf-8 -*-
from datetime import datetime
from collections import defaultdict

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, _get_queryset, render
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.decorators import method_decorator
from django.views.generic.edit import ModelFormMixin
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import FormMixin
from django.views.generic.base import TemplateResponseMixin
from django.views.decorators.http import require_http_methods

from pure_pagination.paginator import Paginator, EmptyPage

from pybb import defaults
from pybb.compat import get_user_model
from pybb.models import (Forum, Topic, Post, Moderator, LogModeration, Attachment, Poll,
                         TopicReadTracker, ForumReadTracker, PollAnswerUser, Subscription)
from pybb.util import load_class, generic, queryset_to_dict, redirect_to_login
from pybb.models.base import markup
from pybb.forms import (PostForm, AdminPostForm, PostsMoveExistingTopicForm,
                        PollAnswerFormSet, AttachmentFormSet, PollForm,
                        ForumForm, ModerationForm, SearchUserForm,
                        get_topic_move_formset, get_topic_merge_formset,
                        get_topic_delete_formset, PostsMoveNewTopicForm)
from pybb.templatetags.pybb_tags import pybb_topic_poll_not_voted
from pybb.helpers import (lookup_users, lookup_post_attachments,
                          lookup_post_topics, lookup_topic_lastposts,
                          load_user_posts)


login_required = load_class(defaults.PYBB_LOGIN_REQUIRED_DECORATOR)


def filter_hidden(request, queryset_or_model):
    """
    Return queryset for model, manager or queryset,
    filtering hidden objects for non authenticated users and staff users.
    """
    queryset = _get_queryset(queryset_or_model)

    return queryset.filter_by_user(request.user)


class ListView(generic.ListView):
    def paginate_queryset(self, queryset, page_size):
        try:
            return super(ListView, self).paginate_queryset(queryset, page_size)
        except EmptyPage:
            raise Http404(ugettext(u'Page is empty.'))


class IndexView(generic.ListView):
    template_name = 'pybb/index.html'
    context_object_name = 'forums'

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)

        forums = queryset_to_dict(filter_hidden(self.request, Forum.objects.filter(forum__isnull=True)))

        for forum in ctx['forums']:
            if forum.forum_id in forums:
                parent_forum = forums[forum.forum_id]

                if not hasattr(parent_forum, 'forums_accessed'):
                    parent_forum.forums_accessed = []

                parent_forum.forums_accessed.append(forum)

        ctx['forums'] = sorted(forums.values(), key=lambda forum: forum.position)

        return ctx

    def get_queryset(self):
        qs = filter_hidden(self.request, (Forum.objects.filter(forum__forum__isnull=True, forum__isnull=False)
                                          .select_related('last_post__topic__forum',
                                                          'last_post__user__profile')
                                          .order_by('forum', 'position')))

        return qs


class ForumCreateView(generic.DetailView, FormMixin):
    form_class = ForumForm
    template_name = 'pybb/forum/create.html'
    pk_url_kwarg = 'forum_id'
    model = Forum
    context_object_name = 'forum'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def get_object(self, queryset=None):
        try:
            self.object = super(ForumCreateView, self).get_object(queryset=queryset)
        except AttributeError:
            self.object = None

        return self.object

    def get_context_data(self, **kwargs):
        data = super(ForumCreateView, self).get_context_data(**kwargs)

        return dict(data, **{
            'form': self.get_form(self.get_form_class()),
        })

    def get_initial(self):
        return {
            'forum': getattr(self, 'object', None)
        }.copy()

    def form_valid(self, form):
        self.forum = form.save()

        return redirect(self.get_success_url())

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ForumCreateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.forum.get_absolute_url()


class ForumUpdateView(generic.UpdateView):
    form_class = ForumForm
    model = Forum
    template_name = 'pybb/forum/update.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        self.object = form.save()

        return redirect(self.get_success_url())

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ForumUpdateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()


class ForumDetailView(ListView):
    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/forum/detail.html'
    paginator_class = Paginator
    url = '^(?P<slug>[\w\-\_]+)/(?:(?P<page>\d+)/)?$'

    def get_context_data(self, **kwargs):
        ctx = super(ForumDetailView, self).get_context_data(**kwargs)

        ctx['forum'] = self.forum

        qs = filter_hidden(self.request,
                           self.forum.forums.select_related('last_post__topic__forum',
                                                            'last_post__user__profile'))
        self.forum.forums_accessed = qs

        lookup_topic_lastposts(ctx[self.context_object_name])
        lookup_users(ctx[self.context_object_name])

        last_posts = []
        for topic in ctx[self.context_object_name]:
            topic.forum = self.forum

            if topic.last_post_id:
                try:
                    last_posts.append(topic.last_post)
                    topic.last_post.topic = topic
                except Post.DoesNotExist:
                    pass

        lookup_users(last_posts)

        return ctx

    def get_queryset(self):
        if not self.forum.is_accessible_by(self.request.user, hidden=False):
            raise Http404

        qs = (self.forum.topics.order_by('-sticky', '-updated')
              .filter_by_user(self.request.user, forum=self.forum))

        return qs

    def get_forum(self):
        self.forum = get_object_or_404(Forum.objects.filter_by_user(self.request.user, hidden=False),
                                       slug=self.kwargs['slug'])

        return self.forum

    def get(self, request, *args, **kwargs):
        forum = self.get_forum()

        if forum.is_hidden() and not self.request.user.is_authenticated():
            return redirect_to_login(request.get_full_path())

        if 'page' in kwargs:
            page = kwargs.get('page', None)

            if page:
                page = int(page)

                if page == 1:
                    return redirect(forum.get_absolute_url(), permanent=True)

        self.object_list = self.get_queryset()

        allow_empty = self.get_allow_empty()

        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(object_list=self.object_list)

        return self.render_to_response(context)


class LogModerationListView(ListView):
    template_name = 'pybb/moderation/logs.html'
    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'logmoderation_list'
    paginator_class = Paginator
    model = LogModeration

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LogModerationListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related()


class TopicsLatestView(ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    paginator_class = Paginator
    context_object_name = 'topic_list'
    template_name = 'pybb/topic/latest.html'
    model = Topic

    def get_queryset(self):
        return (self.model.objects.visible()
                .select_related('forum')
                .order_by('-updated'))

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TopicsLatestView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(TopicsLatestView, self).get_context_data(**kwargs)

        lookup_topic_lastposts(ctx[self.context_object_name])
        lookup_users(ctx[self.context_object_name])

        last_posts = []
        for topic in ctx[self.context_object_name]:
            if topic.last_post_id:
                try:
                    last_posts.append(topic.last_post)
                except Post.DoesNotExist:
                    pass

        lookup_users(last_posts)

        return ctx


class UserPostsView(ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    paginator_class = Paginator
    template_object_name = 'post_list'
    template_name = 'pybb/user/post_list.html'

    def get_queryset(self):
        self.user = get_object_or_404(get_user_model(),
                                      username=self.kwargs['username'])

        qs = (self.user.posts.all()
              .visible(join=False)
              .order_by('-created'))

        return qs

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UserPostsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UserPostsView, self).get_context_data(**kwargs)

        ctx['post_user'] = self.user

        lookup_post_topics(ctx[self.template_object_name])
        load_user_posts(ctx[self.template_object_name], self.user)
        lookup_post_attachments(ctx[self.template_object_name])
        lookup_users([post.topic for post in ctx[self.template_object_name]])

        return ctx


class UserPostsDeleteView(generic.DeleteView):
    template_name = 'pybb/user/posts_delete.html'
    context_object_name = 'post_user'
    slug_url_kwarg = 'username'
    slug_field = 'username'

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UserPostsDeleteView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_context_data(self, **kwargs):
        context = super(UserPostsDeleteView, self).get_context_data(**kwargs)

        posts = (self.object.posts
                 .visible(join=False)
                 .order_by('-created')[:10])

        lookup_post_topics(posts)
        load_user_posts(posts, self.object)
        lookup_post_attachments(posts)
        lookup_users([post.topic for post in posts])

        context['post_list'] = posts
        context['count'] = self.object.posts.visible().count()

        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.object.posts.all().update(deleted=True)

        for topic in Topic.objects.filter(first_post__user=self.object):
            topic.mark_as_deleted()

        messages.success(self.request, _(u'All messages from %(user)s has been deleted') % {
            'user': self.object
        })

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('pybb:user_posts', kwargs={
            'username': self.object.username
        })


class TopicDetailView(ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    paginator_class = Paginator
    template_object_name = 'post_list'
    template_name = 'pybb/topic/list.html'
    url = '^(?P<forum_slug>[\w\-\_]+)/(?P<pk>\d+)-(?P<slug>[\w\-\_]+)(?:\-(?P<page>\d+)/)?$'

    def get(self, request, *args, **kwargs):
        topic = self.get_topic()

        if topic.is_hidden() and not self.request.user.is_authenticated():
            return redirect_to_login(request.get_full_path())

        self.object_list = self.get_queryset()

        allow_empty = self.get_allow_empty()

        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})

        context = self.get_context_data(object_list=self.object_list)

        if (topic.slug != self.kwargs['slug'] or
                ('forum_slug' in self.kwargs and topic.forum.slug != self.kwargs['forum_slug'])):
            return redirect(topic.get_absolute_url(), permanent=True)

        if topic.redirect:
            redirection = topic.redirection

            to_url = redirection.to_topic.get_absolute_url()

            if redirection.is_type_permanent():
                return redirect(to_url, permanent=True)
            elif redirection.is_type_expiring():
                if redirection.is_expired():
                    raise Http404

                return redirect(to_url)
            elif redirection.is_type_no():
                raise Http404

        page = kwargs.get('page', None)

        if page:
            page = int(page)

            if page == 1:
                return redirect(topic.get_absolute_url(), permanent=True)

        topic.views += 1

        Topic.objects.filter(pk=topic.pk).update(views=topic.views)

        return self.render_to_response(context)

    def get_topic(self):
        self.topic = get_object_or_404(Topic.objects.all().select_related('forum'),
                                       pk=self.kwargs['pk'])

        return self.topic

    def get_queryset(self):
        if not self.topic.is_accessible_by(self.request.user):
            raise Http404

        qs = (self.topic.posts.all()
              .filter_by_user(self.topic, self.request.user)
              .order_by('created'))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super(TopicDetailView, self).get_context_data(**kwargs)

        self.topic.post_counts = {
            self.request.user: ctx['paginator'].count
        }

        page_number = ctx['page_obj'].number

        start = page_number

        if page_number > 1:
            start = (start - 1) * ctx['paginator'].per_page + 1

        for idx, post in enumerate(ctx[self.template_object_name], start):
            post.topic = self.topic
            post.index = idx

        ctx['topic'] = self.topic
        ctx['subscription_types'] = Subscription.TYPE_CHOICES
        ctx['redirect'] = self.request.GET.get('redirect', False)

        if self.request.user.is_authenticated():
            self.request.user.is_moderator = self.topic.is_moderated_by(self.request.user)

            self.request.user.is_subscribed = self.topic.is_subscribed_by(self.request.user)

            self.topic.mark_as_read(self.request.user)

            if (self.topic.poll_id and
                    pybb_topic_poll_not_voted(self.topic, self.request.user)):
                try:
                    ctx['poll_form'] = PollForm(self.topic.poll)
                except Poll.DoesNotExist:
                    pass

            try:
                subscription = self.request.user.subscription_set.get(topic=self.topic)
                ctx['current_subscription_type'] = ctx['subscription_types'][subscription.type]
            except Subscription.DoesNotExist:
                ctx['current_subscription_type'] = Subscription.TYPE_CHOICES[0]

        if defaults.PYBB_FREEZE_FIRST_POST:
            ctx['first_post'] = self.topic.head
        else:
            ctx['first_post'] = None

        lookup_users(ctx[self.template_object_name])
        lookup_post_attachments(ctx[self.template_object_name])

        return ctx


class PostUpdateMixin(object):
    def get_form_class(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return AdminPostForm

        return PostForm

    def get_context_data(self, **kwargs):
        ctx = super(PostUpdateMixin, self).get_context_data(**kwargs)

        instance = None

        if getattr(self, 'object'):
            instance = self.object.topic.poll

        if 'pollformset' not in kwargs:
            pollformset = PollAnswerFormSet(instance=instance)

            ctx['pollformset'] = pollformset

        return ctx

    def get_form_kwargs(self):
        form_kwargs = super(PostUpdateMixin, self).get_form_kwargs()

        if self.request.user.is_staff and self.object:
            form_kwargs['initial']['login'] = self.object.user

        return form_kwargs

    def form_valid(self, form):
        success = True

        with getattr(transaction, 'atomic', getattr(transaction, 'commit_manually', None))():
            sid = transaction.savepoint()

            try:
                self.object = form.save()

                if self.object.topic.poll:
                    if self.object.topic.head == self.object:
                        pollformset = PollAnswerFormSet(self.request.POST,
                                                        instance=self.object.topic.poll)
                        if pollformset.is_valid():
                            pollformset.save()
                        else:
                            success = False
                    else:
                        success = True

                if success:
                    transaction.savepoint_commit(sid)
                else:
                    transaction.savepoint_rollback(sid)
            except Exception, e:
                transaction.savepoint_rollback(sid)
                raise e

        if success:
            return super(ModelFormMixin, self).form_valid(form)

        context = self.get_context_data(form=form,
                                        pollformset=pollformset)

        return self.render_to_response(context)


class PostCreateView(PostUpdateMixin, generic.CreateView):
    template_name = 'pybb/post/create.html'

    def get_form_kwargs(self):
        ip = self.request.META.get('REMOTE_ADDR', '')
        form_kwargs = super(PostCreateView, self).get_form_kwargs()
        form_kwargs.update(dict(topic=self.topic, forum=self.forum, user=self.user,
                                ip=ip, initial={}))

        if self.user.is_staff:
            form_kwargs['initial']['login'] = self.user

        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super(PostCreateView, self).get_context_data(**kwargs)

        ctx['forum'] = self.forum

        ctx['topic'] = self.topic

        ctx['post_list'] = []

        if self.topic:
            qs = (self.topic.posts.all()
                  .select_related('user__profile')
                  .order_by('-created')
                  .filter_by_user(self.topic, self.request.user))

            ctx['post_count'] = qs.count()

            posts = qs[:defaults.PYBB_POST_LIST_SIZE]

            for post in posts:
                post.topic = self.topic

            ctx['post_list'] = posts
            ctx['post_page_size'] = defaults.PYBB_POST_LIST_SIZE

        return ctx

    def get_success_url(self):
        if (not self.request.user.is_authenticated() and
                defaults.PYBB_PREMODERATION):
            return reverse('pybb:index')

        return self.object.get_anchor_url(self.request.user)

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            self.user = request.user
        else:
            if not defaults.PYBB_ENABLE_ANONYMOUS_POST:
                return redirect_to_login(request.get_full_path())

            User = get_user_model()

            self.user, new = User.objects.get_or_create(username=defaults.PYBB_ANONYMOUS_USERNAME)

        self.forum = None
        self.topic = None

        data = request.POST or {}

        forum_id = kwargs.get('forum_id', None) or data.get('forum_id', None)

        topic_id = kwargs.get('topic_id', None) or data.get('topic_id', None)

        if forum_id:
            self.forum = get_object_or_404(filter_hidden(request, Forum), pk=forum_id)
        elif topic_id:
            self.topic = get_object_or_404(Topic.objects.visible(), pk=topic_id)

            if not self.topic.is_accessible_by(request.user):
                raise Http404

            if self.topic.closed:
                raise PermissionDenied

        result = all([load_class(pre_post_create_filter)(
            topic=self.topic,
            request=request,
            forum=self.forum,
        ).is_allowed(request.user) for pre_post_create_filter in defaults.PYBB_PRE_POST_CREATE_FILTERS])

        if not result:
            raise PermissionDenied

        return super(PostCreateView, self).dispatch(request, *args, **kwargs)


class PostUpdateView(PostUpdateMixin, generic.UpdateView):
    model = Post
    context_object_name = 'post'
    template_name = 'pybb/post/update.html'

    def get_form_kwargs(self):
        form_kwargs = super(PostUpdateView, self).get_form_kwargs()
        form_kwargs.update(dict(actor=self.request.user))

        return form_kwargs

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(PostUpdateView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        post = super(PostUpdateView, self).get_object(queryset)

        if not post.is_editable_by(self.request.user, 'can_change_post'):
            raise PermissionDenied

        return post

    def get_success_url(self, *args, **kwargs):
        if self.request.user.pk != self.object.user_id:
            LogModeration.objects.log(
                user=self.request.user,
                obj=self.object,
                action_flag=LogModeration.ACTION_FLAG_CHANGE,
                user_ip=self.request.META['REMOTE_ADDR'],
                level=LogModeration.LEVEL_MEDIUM,
            )

        return super(PostUpdateView, self).get_success_url(*args, **kwargs)


class PostsCreateView(generic.RedirectView):
    http_method_names = ['post']

    def get_redirect_url(self, **kwargs):
        if 'topic_id' not in self.request.POST:
            raise Http404

        try:
            pk = int(self.request.POST.get('topic_id', None))
        except ValueError:
            raise Http404

        return reverse('pybb:post_create', kwargs={
            'topic_id': pk
        })


class PostRedirectView(generic.RedirectView):
    http_method_names = ['post', 'get']

    def get_redirect_url(self, **kwargs):
        if self.request.method == 'POST':
            if 'post_id' not in self.request.POST:
                raise Http404

            try:
                pk = int(self.request.POST.get('post_id', None))
            except ValueError:
                raise Http404
        else:
            pk = kwargs.get('post_id', None)

        if not pk:
            raise Http404

        post = get_object_or_404(Post, pk=pk)

        if not post.is_accessible_by(self.request.user):
            raise PermissionDenied

        return post.get_anchor_url(self.request.user, {'redirect': 1})


class PostModerateView(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])

        if not post.topic.is_moderated_by(self.request.user):
            raise PermissionDenied

        post.on_moderation = not post.on_moderation
        post.save()

        if post.on_moderation:
            change_message = _('%s is now on moderation') % post
        else:
            change_message = _('%s is not on moderation anymore') % post

        LogModeration.objects.log(
            user=self.request.user,
            obj=post,
            action_flag=LogModeration.ACTION_FLAG_CHANGE,
            user_ip=self.request.META['REMOTE_ADDR'],
            level=LogModeration.LEVEL_MEDIUM,
            change_message=change_message
        )

        return post.get_anchor_url(self.request.user)


class PostDeleteView(generic.DeleteView):
    template_name = 'pybb/post/delete.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post.objects.select_related('topic', 'topic__forum'),
                                 pk=self.kwargs['pk'])

        self.topic = post.topic
        self.forum = post.topic.forum

        if (not self.topic.is_moderated_by(self.request.user, 'can_delete_post')
                and not post.user == self.request.user):
            raise PermissionDenied

        return post

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.deleted:
            self.object.mark_as_deleted(user=self.request.user)
        else:
            self.object.mark_as_undeleted()

        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.object.deleted:
            messages.success(self.request, _('Your post has been successfully deleted'))
        else:
            messages.success(self.request, _('Your post has been successfully restored'))

        if self.request.user.pk != self.object.user_id:
            LogModeration.objects.log(
                user=self.request.user,
                obj=self.object,
                action_flag=LogModeration.ACTION_FLAG_DELETION,
                user_ip=self.request.META['REMOTE_ADDR'],
                level=LogModeration.LEVEL_HIGH,
            )

        try:
            Topic.objects.filter(deleted=False).get(pk=self.topic.id)
        except Topic.DoesNotExist:
            return self.forum.get_absolute_url()
        else:
            return self.topic.get_absolute_url()


class PostsMoveView(generic.FormView):
    http_method_names = ['post']
    choice = {
        '0': ('new_topic_form', PostsMoveNewTopicForm),
        '1': ('existing_topic_form', PostsMoveExistingTopicForm),
    }

    template_name = 'pybb/post/move.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PostsMoveView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return kwargs

    def post(self, request, *args, **kwargs):
        forms = {}
        context = {}

        post_ids = self.request.POST.getlist('post_ids')

        context['post_ids'] = post_ids

        posts = (Post.objects.filter(pk__in=post_ids)
                 .select_related('topic', 'topic__forum'))

        context['posts'] = posts

        if not len(posts):
            raise Http404

        for post in posts:
            if (not post.topic.is_moderated_by(self.request.user, 'can_move_post')):
                raise PermissionDenied

        for key, (form_name, form_class) in self.choice.items():
            form = form_class(request.POST if 'submit' in request.POST else None,
                              posts=posts, user=request.user)

            forms[key] = form
            context[form_name] = form

        if 'submit' in request.POST:
            choice = request.POST.get('choice', '0')

            if choice in forms:
                form = forms[choice]

                if form.is_valid():
                    topic = form.save()

                    return redirect(topic.get_absolute_url())

        return self.render_to_response(context)


class TopicBatchView(generic.FormView):
    http_method_names = ['post']

    def get_context_data(self, **kwargs):
        return dict(super(TopicBatchView, self).get_context_data(**kwargs), **{
            'topic_ids': self.request.POST.getlist('topic_ids')
        })

    def get_initial(self):
        return {}

    def get_queryset(self):
        return Topic.objects.visible().filter(pk__in=self.request.POST.getlist('topic_ids'))

    def get_form_class(self):
        topics = self.get_queryset()

        if not len(topics):
            raise Http404

        for topic in topics:
            if (not topic.is_moderated_by(self.request.user, self.permission_name)):
                raise PermissionDenied

        return self.get_formset_class(topics=topics)

    def get_formset_class(self, **kwargs):
        pass

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = {'initial': self.get_initial()}
        if self.request.method in ('POST', 'PUT') and 'submit' in self.request.POST:
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if 'submit' in request.POST:
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, formset):
        topics = []

        for form in formset:
            topics.append((form.topic, form.save()))

        return redirect(self.get_success_url(topics))

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TopicBatchView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, topics):
        return reverse('pybb:index')


class TopicMergeView(TopicBatchView):
    template_name = 'pybb/topic/merge.html'
    permission_name = 'can_merge_topic'

    def get_formset_class(self, **kwargs):
        return get_topic_merge_formset(**kwargs)

    def get_success_url(self, topics):
        for old_topic, new_topic in topics:
            messages.success(self.request, _(u'<a href="%(old_topic_url)s">%(old_topic)s</a> successfully merged to <a href="%(new_topic_url)s">%(new_topic)s</a>') % {
                'old_topic_url': old_topic.get_absolute_url(),
                'old_topic': old_topic,
                'new_topic_url': new_topic.get_absolute_url(),
                'new_topic': new_topic
            })

        return reverse('pybb:index')


class TopicMoveView(TopicBatchView):
    template_name = 'pybb/topic/move.html'
    permission_name = 'can_move_topic'

    def get_formset_class(self, **kwargs):
        return get_topic_move_formset(**kwargs)

    def get_success_url(self, topics):
        for old_topic, new_topic in topics:
            messages.success(self.request, _(u'<a href="%(old_topic_url)s">%(old_topic)s</a> successfully moved to <a href="%(new_topic_url)s">%(new_topic)s</a>') % {
                'old_topic_url': old_topic.get_absolute_url(),
                'old_topic': old_topic,
                'new_topic_url': new_topic.get_absolute_url(),
                'new_topic': new_topic
            })

        return reverse('pybb:index')


class TopicsDeleteView(TopicBatchView):
    template_name = 'pybb/topic/delete.html'
    permission_name = 'can_delete_topic'

    def get_queryset(self):
        return Topic.objects.filter(pk__in=self.request.POST.getlist('topic_ids'))

    def get_context_data(self, **kwargs):
        context = dict(super(TopicBatchView, self).get_context_data(**kwargs), **{
            'topic_ids': self.request.POST.getlist('topic_ids'),
        })

        formset = context['form']

        topics = defaultdict(list)

        for form in formset.forms:
            if form.topic.deleted:
                topics['to_restore'].append(form)
            else:
                topics['to_delete'].append(form)

        context['topics'] = dict(topics)

        return context

    def get_formset_class(self, **kwargs):
        return get_topic_delete_formset(**kwargs)

    def form_valid(self, formset):
        topics = []

        for form in formset:
            topics.append(form.save())

        return redirect(self.get_success_url(topics))

    def get_success_url(self, topics):
        sorted_topics = defaultdict(list)

        for topic in topics:
            if topic.deleted:
                sorted_topics['deleted'].append(topic)
            else:
                sorted_topics['restored'].append(topic)

        actions = {
            'deleted': _('deleted'),
            'restored': _('restored'),
        }

        for key in ('deleted', 'restored', ):
            if key in sorted_topics:
                messages.success(self.request, _(u'%(topics)s successfully %(action)s') % {
                    'topics': ' '.join([u'<a href="%(topic_url)s">%(topic)s</a>' % {
                        'topic_url': topic.get_absolute_url(),
                        'topic': topic
                    } for topic in sorted_topics[key]]),
                    'action': actions[key]
                })

        return reverse('pybb:index')


class TopicDeleteView(generic.DeleteView):
    template_name = 'pybb/topic/delete.html'
    context_object_name = 'topic'

    def get_object(self, queryset=None):
        topic = get_object_or_404(Topic.objects.select_related('forum'),
                                  pk=self.kwargs['pk'])

        self.topic = topic
        self.forum = topic.forum

        if not self.topic.is_moderated_by(self.request.user, 'can_delete_topic'):
            raise PermissionDenied

        return topic

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.deleted:
            self.object.mark_as_deleted()
        else:
            self.object.mark_as_undeleted()

        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.object.deleted:
            LogModeration.objects.log(
                user=self.request.user,
                obj=self.object,
                action_flag=LogModeration.ACTION_FLAG_DELETION,
                user_ip=self.request.META['REMOTE_ADDR'],
                level=LogModeration.LEVEL_HIGH,
            )

        return self.forum.get_absolute_url()


class TopicActionBaseView(generic.View):
    def get_topic(self):
        topic = get_object_or_404(Topic, pk=self.kwargs['pk'])

        if not self.is_allowed(topic, self.request.user):
            raise PermissionDenied

        return topic

    def is_allowed(self, topic, user, permission=None):
        return topic.is_moderated_by(user, permission=permission)

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        self.topic = self.get_topic()
        self.action(self.topic)

        LogModeration.objects.log(
            user=self.request.user,
            obj=self.topic,
            action_flag=LogModeration.ACTION_FLAG_CHANGE,
            user_ip=self.request.META['REMOTE_ADDR'],
            level=LogModeration.LEVEL_HIGH,
            change_message=self.get_change_message(self.topic)
        )

        return redirect(self.topic.get_absolute_url())

    def get_change_message(self, topic):
        return ''


class TopicStickView(TopicActionBaseView):
    def action(self, topic):
        topic.sticky = True
        topic.save()

    def is_allowed(self, topic, user):
        return super(TopicStickView, self).is_allowed(topic, user, 'can_stick_topic')

    def get_change_message(self, topic):
        return _('Stick topic %s') % topic.name


class TopicUnstickView(TopicActionBaseView):
    def action(self, topic):
        topic.sticky = False
        topic.save()

    def is_allowed(self, topic, user):
        return super(TopicUnstickView, self).is_allowed(topic, user, 'can_unstick_topic')

    def get_change_message(self, topic):
        return _('Unstick topic %s') % topic.name


class TopicCloseView(TopicActionBaseView):
    def action(self, topic):
        topic.closed = True
        topic.save()

    def is_allowed(self, topic, user):
        return super(TopicCloseView, self).is_allowed(topic, user, 'can_close_topic')

    def get_change_message(self, topic):
        return _('Close topic %s') % topic.name


class TopicTrackerRedirectView(generic.RedirectView):
    http_method_names = ['get']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TopicTrackerRedirectView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        topic = get_object_or_404(Topic, pk=kwargs.get('topic_id'))

        tracker = None

        try:
            tracker = TopicReadTracker.objects.get(topic=topic, user=self.request.user)
        except TopicReadTracker.DoesNotExist:
            try:
                tracker = ForumReadTracker.objects.get(forum=topic.forum, user=self.request.user)
            except ForumReadTracker.DoesNotExist:
                pass

        if not tracker:
            return topic.get_absolute_url()

        try:
            post = topic.posts.visible().filter(created__gte=tracker.time_stamp).order_by('created')[0]
        except IndexError:
            try:
                return topic.last_post.get_absolute_url()
            except Post.DoesNotExist:
                return topic.get_absolute_url()
        else:
            return post.get_anchor_url(user=self.request.user)


class TopicOpenView(TopicActionBaseView):
    def action(self, topic):
        topic.closed = False
        topic.save()

    def is_allowed(self, topic, user):
        return super(TopicOpenView, self).is_allowed(topic, user, 'can_open_topic')

    def get_change_message(self, topic):
        return _('Open topic %s') % topic.name


class TopicPollVoteView(generic.UpdateView):
    queryset = Topic.objects.visible().filter(poll__isnull=False).select_related('poll')
    http_method_names = ['post', ]
    form_class = PollForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TopicPollVoteView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        kwargs['poll'] = self.object.poll
        return kwargs

    def form_valid(self, form):
        # already voted
        if not pybb_topic_poll_not_voted(self.object.poll, self.request.user):
            return HttpResponseBadRequest()

        answers = form.cleaned_data['answers']
        for answer in answers:
            # poll answer from another topic
            if answer.poll != self.object.poll:
                return HttpResponseBadRequest()

            PollAnswerUser.objects.create(poll_answer=answer,
                                          user=self.request.user)
        return super(ModelFormMixin, self).form_valid(form)

    def form_invalid(self, form):
        return self.object.get_absolute_url()

    def get_success_url(self):
        return self.object.get_absolute_url()


class ModeratorListView(generic.ListView):
    paginate_by = defaults.PYBB_TOPIC_PAGE_SIZE
    paginator_class = Paginator
    template_name = 'pybb/moderation/moderator/list.html'
    context_object_name = 'moderator_list'
    model = Moderator

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ModeratorListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return dict(super(ModeratorListView, self).get_context_data(**kwargs), **{
            'object': self.object
        })

    def get_object(self):
        self.object = get_object_or_404(Forum, pk=self.kwargs.get('pk'))

        return self.object

    def get_queryset(self):
        return self.model.objects.filter(forum=self.get_object())


class ModeratorDetailView(generic.DetailView, FormMixin):
    template_name = 'pybb/moderation/moderator/detail.html'
    model = Moderator
    pk_url_kwarg = 'moderator_id'
    context_object_name = 'moderator'
    form_class = ModerationForm

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ModeratorDetailView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.forum = get_object_or_404(Forum, pk=self.kwargs.get('forum_id'))

        return self.model.objects.filter(forum=self.forum)

    def get_context_data(self, **kwargs):
        return dict(super(ModeratorDetailView, self).get_context_data(**kwargs), **{
            'forum': self.forum,
            'forms': self.get_forms(self.get_form_class()),
        })

    def get_forms(self, form_class):
        return [self.get_form(form_class,
                              permissions=self.get_permissions(defaults.PYBB_FORUM_PERMISSIONS, Forum),
                              obj=self.forum,
                              user=self.object.user),
                self.get_form(form_class,
                              permissions=self.get_permissions(defaults.PYBB_USER_PERMISSIONS),
                              user=self.object.user)]

    def get_form(self, form_class, **kwargs):
        return form_class(**dict(self.get_form_kwargs(), **kwargs))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data(object=self.object)

        forms = context['forms']

        if all([form.is_valid() for form in forms]):
            return self.form_valid(forms)

        return self.form_invalid(forms)

    def form_valid(self, forms):
        for form in forms:
            form.save(self.object.user)

        return redirect(self.get_success_url())

    def get_permissions(self, codenames, model_class=None):
        filters = {
            'codename__in': codenames
        }

        if model_class:
            filters['content_type'] = ContentType.objects.get_for_model(model_class)

        return Permission.objects.filter(**filters)

    def get_success_url(self):
        names = [permission.name
                 for permission in self.object.user.user_permissions.all()]

        change_message = _('Changed permissions:\n %s') % '\n'.join(names)

        LogModeration.objects.log(
            user=self.request.user,
            obj=self.forum,
            action_flag=LogModeration.ACTION_FLAG_CHANGE,
            target=self.object.user,
            user_ip=self.request.META['REMOTE_ADDR'],
            level=LogModeration.LEVEL_MEDIUM,
            change_message=change_message
        )

        messages.success(self.request, _(u'Permissions for moderator "%(username)s" successfully saved') % {
            'username': self.object.user.username
        })

        return reverse('pybb:moderator_detail', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': self.object.pk
        })


class ModeratorCreateView(ModeratorDetailView):
    template_name = 'pybb/moderation/moderator/create.html'
    model = Forum
    pk_url_kwarg = 'forum_id'
    context_object_name = 'forum'

    def get_context_data(self, **kwargs):
        self.forum = self.object

        return super(ModeratorCreateView, self).get_context_data(**kwargs)

    def get_forms(self, form_class):
        forms = [self.get_form(SearchUserForm),
                 self.get_form(form_class,
                               permissions=self.get_permissions(defaults.PYBB_FORUM_PERMISSIONS, Forum),
                               obj=self.forum),
                 self.get_form(form_class,
                               permissions=self.get_permissions(defaults.PYBB_USER_PERMISSIONS))]

        return forms

    def get_queryset(self):
        return self.model.objects.all()

    def form_valid(self, forms):
        user_form = forms.pop(0)
        user = user_form.get_user(user_form.cleaned_data['username'])

        moderator = Moderator.objects.create(forum=self.forum, user=user)

        for form in forms:
            form.save(user)

        return redirect(self.get_success_url(moderator))

    def get_success_url(self, moderator):
        LogModeration.objects.log(
            user=self.request.user,
            obj=self.forum,
            action_flag=LogModeration.ACTION_FLAG_ADDITION,
            target=moderator.user,
            user_ip=self.request.META['REMOTE_ADDR'],
            level=LogModeration.LEVEL_HIGH
        )

        messages.success(self.request, _(u'New moderator "%(username)s" created') % {
            'username': moderator.user.username
        })

        return reverse('pybb:moderator_detail', kwargs={
            'forum_id': self.forum.pk,
            'moderator_id': moderator.pk
        })


class ModeratorDeleteView(generic.DeleteView):
    template_name = 'pybb/moderation/moderator/delete.html'
    context_object_name = 'moderator'
    model = Moderator
    pk_url_kwarg = 'moderator_id'

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ModeratorDeleteView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        self.forum = get_object_or_404(Forum, pk=self.kwargs['forum_id'])

        moderator = get_object_or_404(self.model.objects.filter(forum=self.forum),
                                      pk=self.kwargs[self.pk_url_kwarg])

        return moderator

    def get_success_url(self):
        LogModeration.objects.log(
            user=self.request.user,
            obj=self.forum,
            action_flag=LogModeration.ACTION_FLAG_DELETION,
            target=self.object.user,
            user_ip=self.request.META['REMOTE_ADDR'],
            level=LogModeration.LEVEL_HIGH
        )

        return reverse('pybb:moderator_list', kwargs={
            'pk': self.forum.pk
        })

    def get_context_data(self, **kwargs):
        return dict(super(ModeratorDeleteView, self).get_context_data(**kwargs), **{
            'forum': self.forum
        })


class SubscriptionChangeView(generic.RedirectView):
    http_method_names = ['post']
    permanent = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SubscriptionChangeView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        if 'topic_ids' not in self.request.POST or 'type' not in self.request.POST:
            raise Http404

        try:
            type = int(self.request.POST['type'])
        except ValueError:
            raise Http404

        types = dict(Subscription.TYPE_CHOICES)

        if type not in types:
            raise Http404

        topic_ids = self.request.POST.getlist('topic_ids')

        subscriptions = (Subscription.objects.filter(topic__in=topic_ids,
                                                     user=self.request.user)
                         .exclude(type=type)
                         .select_related('topic'))

        subscriptions.update(type=type)

        messages.success(self.request, _(u'Your subscriptions has been updated: %(type)s') % {
            'type': types[type]
        })

        return reverse('pybb:subscription_list')


class SubscriptionDeleteView(generic.RedirectView):
    http_method_names = ['post']
    permanent = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SubscriptionDeleteView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        if 'topic_ids' not in self.request.POST and 'topic_id' not in self.request.POST:
            raise Http404

        topic = None

        if 'topic_ids' in self.request.POST:
            topic_ids = self.request.POST.getlist('topic_ids')
        else:
            topic_id = self.request.POST.get('topic_id')

            topic_ids = [topic_id, ]

            topic = get_object_or_404(Topic, pk=topic_id)

        Subscription.objects.filter(topic__in=topic_ids, user=self.request.user).delete()

        if not topic:
            messages.success(self.request, _(u'Your subscriptions has been deleted'))

            return reverse('pybb:subscription_list')

        messages.success(self.request, _(u'Your subscription to %(topic)s has been deleted') % {
            'topic': topic
        })

        return topic.get_absolute_url()


class SubscriptionListView(generic.ListView):
    template_name = 'pybb/user/subscription_list.html'
    context_object_name = 'subscription_list'
    model = Subscription
    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    paginator_class = Paginator

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SubscriptionListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SubscriptionListView, self).get_context_data(**kwargs)

        topic_list = []
        for subscription in context[self.context_object_name]:
            topic = subscription.topic
            topic.subscription = subscription

            topic_list.append(topic)

        context['topic_list'] = topic_list

        lookup_topic_lastposts(topic_list)
        lookup_users(topic_list)

        last_posts = []
        for topic in topic_list:
            if topic.last_post_id:
                try:
                    last_posts.append(topic.last_post)
                except Post.DoesNotExist:
                    pass

        lookup_users(last_posts)

        context['subscription_types'] = Subscription.TYPE_CHOICES

        return context

    def get_queryset(self):
        qs = (self.model.objects.order_by('-topic__updated')
              .filter(user=self.request.user)
              .select_related('topic__forum')
              .visible())

        return qs


@require_http_methods(['POST'])
@login_required
def create_subscription(request):
    try:
        topic_id = request.POST.get('topic_id', None)
        type = request.POST.get('type', Subscription.TYPE_NO_ALERT)

        if not topic_id:
            raise PermissionDenied

        topic_id = int(topic_id)
    except ValueError:
        raise PermissionDenied

    topic = get_object_or_404(Topic, pk=topic_id)

    subscription, created = Subscription.objects.get_or_create(user=request.user,
                                                               topic=topic)

    subscription.type = type
    subscription.save()

    if created:
        messages.success(request, _(u'Your subscription to %(topic)s has been created: %(type)s') % {
            'topic': topic,
            'type': subscription.get_type_display()
        })
    else:
        messages.success(request, _(u'Your subscription to %(topic)s has been updated: %(type)s') % {
            'topic': topic,
            'type': subscription.get_type_display()
        })

    return redirect(topic.get_absolute_url())


@require_http_methods(['POST'])
@login_required
def post_preview(request, template_name='pybb/post/template.html'):
    content = request.POST.get('data')

    post = Post(body=content, user=request.user)
    post.body_html = markup(content, obj=post)
    post.created = datetime.now()

    return render(request, template_name, {
        'post': post
    })


class ForumMarkAsReadView(generic.View):
    model = ForumReadTracker

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ForumMarkAsReadView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.model.objects.mark_as_read(request.user, filter_hidden(request, Forum))

        TopicReadTracker.objects.filter(user=request.user).delete()

        Subscription.objects.filter(user=request.user).update(sent=False)

        messages.success(request, _('All forums marked as read'), fail_silently=True)

        return redirect(reverse('pybb:index'))

    def post(self, request, *args, **kwargs):
        try:
            forum_id = int(request.POST.get('forum_id', None))
        except ValueError:
            raise PermissionDenied
        else:
            parent_forum = get_object_or_404(filter_hidden(request, Forum), pk=forum_id)

            forums = [parent_forum, ] + list(parent_forum.forums.all())

            self.model.objects.mark_as_read(request.user, forums)

            for forum in forums:
                TopicReadTracker.objects.filter(user=request.user, topic__forum=forum).delete()

                Subscription.objects.filter(user=request.user, topic__forum=forum).update(sent=False)

            messages.success(request, _(u'Forum %s has been marked as read') % parent_forum, fail_silently=True)

            return redirect(parent_forum.get_absolute_url())


class AttachmentDeleteView(generic.DeleteView):
    template_name = 'pybb/attachment/delete.html'
    context_object_name = 'attachment'
    model = Attachment

    def get_object(self, queryset=None):
        attachment = get_object_or_404(self.model,
                                       pk=self.kwargs['pk'])

        if attachment.post_id:
            if not attachment.post.is_editable_by(self.request.user, 'can_change_attachment'):
                raise PermissionDenied
        else:
            if not attachment.user == self.request.user:
                raise PermissionDenied

        return attachment

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AttachmentDeleteView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if not self.request.is_ajax():
            return redirect(self.get_success_url())

        return HttpResponse('Ok')

    def get_success_url(self):
        if self.object.post_id:
            return self.object.post.get_absolute_url()

        return reverse('pybb:index')


class AttachmentListView(TemplateResponseMixin, generic.View):
    template_name = 'pybb/attachment/list.html'
    form_class = AttachmentFormSet
    http_method_names = ['post']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AttachmentListView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.request = request

        ctx = {}

        try:
            post_hash = self.request.POST['post_hash']
        except ValueError:
            raise Http404

        ctx['post_hash'] = post_hash

        try:
            self.object = Post.objects.get(hash=post_hash)
        except Post.DoesNotExist:
            self.object = None
        else:
            if not self.object.is_editable_by(request.user, 'can_change_attachment'):
                raise Http404

        if 'submit' in self.request.POST:
            aformset = self.form_class(self.request.POST, self.request.FILES)

            if aformset.is_valid():
                instances = aformset.save(commit=False)

                for instance in instances:
                    instance.post_hash = post_hash

                    if self.object:
                        instance.post = self.object

                    instance.user = self.request.user
                    instance.save()

                aformset = self.form_class()
        else:
            aformset = self.form_class()

        ctx['aformset'] = aformset

        if self.object:
            ctx['attachments'] = self.object.attachments.all()
        else:
            ctx['attachments'] = Attachment.objects.filter(post_hash=post_hash)

        return self.render_to_response(ctx)
