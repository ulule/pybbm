from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

from pybb.views.base import (PostCreateView as BasePostCreateView,
                             TopicDetailView as BaseTopicDetailView,
                             PostsCreateView as BasePostsCreateView)
from pybb.contrib.quotes.exceptions import QuoteException
from pybb.contrib.quotes.models import quote
from pybb.models import Post, Topic
from pybb import defaults

from pybb.util import generic, load_class


def make_session_key(topic):
    return 'topic:%d:quote_ids' % topic.pk


def get_posts_quoted(request, topic):
    session_key = make_session_key(topic)

    return (topic.posts.filter_by_user(topic, request.user)
            .filter(id__in=request.session.get(session_key, [])))


class TopicDetailView(BaseTopicDetailView):
    def get_context_data(self, **kwargs):
        ctx = super(TopicDetailView, self).get_context_data(**kwargs)

        return dict(ctx, **{
            'posts_quoted': get_posts_quoted(self.request, self.topic)
        })


class PostsCreateView(BasePostsCreateView):
    http_method_names = ['post']

    def get_redirect_url(self, **kwargs):
        url = super(PostsCreateView, self).get_redirect_url(**kwargs)

        if not 'quote_id' in self.request.POST:
            return url

        try:
            quote_id = int(self.request.POST.get('quote_id', None))
        except ValueError:
            raise Http404

        return url + u'?quote_id=%s' % quote_id


class PostCreateView(BasePostCreateView):
    def get_form_kwargs(self):
        form_kwargs = super(PostCreateView, self).get_form_kwargs()

        if self.request.method == 'GET':
            post_quoted = {}

            if 'quote_id' in self.request.GET:
                try:
                    quote_id = int(self.request.GET.get('quote_id'))
                except TypeError:
                    raise Http404
                else:
                    post = get_object_or_404(Post, pk=quote_id)

                    post_quoted[post.pk] = post

            if self.topic:
                for post in get_posts_quoted(self.request, self.topic):
                    post_quoted[post.pk] = post

            if len(post_quoted.keys()):
                form_kwargs['initial']['body'] = '\n'.join([quote(post, post.user.username)
                                                            for post_id, post in post_quoted.iteritems()])

        return form_kwargs

    def form_valid(self, form):
        try:
            response = super(PostCreateView, self).form_valid(form)

            if self.topic:
                session_key = make_session_key(self.topic)

                if session_key in self.request.session:
                    del self.request.session[session_key]

            return response
        except QuoteException, e:
            messages.error(self.request, e.message)

        return self.form_invalid(form)


class QuoteView(generic.View):
    http_method_names = ['post']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuoteView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            topic = Topic.objects.get(pk=request.POST['topic_id'])

            post = topic.posts.filter_by_user(topic, request.user).get(pk=request.POST['post_id'])
        except (Topic.DoesNotExist, Post.DoesNotExist, ValueError):
            raise Http404
        else:
            result = all([load_class(pre_post_create_filter)(
                topic=topic,
                request=request,
                forum=topic.forum,
            ).is_allowed(request.user) for pre_post_create_filter in defaults.PYBB_PRE_POST_CREATE_FILTERS])

            if not result:
                raise PermissionDenied

            session_key = make_session_key(topic)

            post_ids = request.session.get(session_key, [])

            if post.pk in post_ids:
                post_ids.remove(post.pk)
            else:
                post_ids.append(post.pk)

            request.session[session_key] = post_ids

            if request.is_ajax():
                return HttpResponse('Ok')

            return redirect(post.get_anchor_url(request.user))
