# -*- coding: utf-8 -*-
import inspect
import copy

from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.forms.formsets import BaseFormSet

from pybb.models import (Topic, Post, Attachment, TopicRedirection,
                         PollAnswer, Forum, Poll)
from pybb.compat import User
from pybb.proxies import UserObjectPermission
from pybb import defaults
from pybb.util import tznow, load_class

from autoslug.settings import slugify


class AttachmentForm(forms.ModelForm):
    class Meta(object):
        model = Attachment
        fields = ('file', )

    def clean_file(self):
        if self.cleaned_data['file'].size > defaults.PYBB_ATTACHMENT_SIZE_LIMIT:
            raise forms.ValidationError(_('Attachment is too big'))
        return self.cleaned_data['file']

AttachmentFormSet = inlineformset_factory(Post, Attachment, extra=1, form=AttachmentForm)


class PollAnswerForm(forms.ModelForm):
    class Meta:
        model = PollAnswer
        fields = ('text', )


class BasePollAnswerFormset(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        forms_cnt = len(self.initial_forms) + len([form for form in self.extra_forms if form.has_changed()]) - len(self.deleted_forms)

        if forms_cnt > defaults.PYBB_POLL_MAX_ANSWERS:
            raise forms.ValidationError(_('You can''t add more than %s answers for poll') % defaults.PYBB_POLL_MAX_ANSWERS)

        if forms_cnt < 2:
            raise forms.ValidationError(_('Add two or more answers for this poll'))


PollAnswerFormSet = inlineformset_factory(Poll, PollAnswer, extra=2, max_num=defaults.PYBB_POLL_MAX_ANSWERS,
                                          form=PollAnswerForm, formset=BasePollAnswerFormset)


class PostForm(forms.ModelForm):
    error_messages = {
        'duplicate': _("A topic with that name already exists."),
    }

    name = forms.CharField(label=_('Subject'))

    body = forms.CharField(label=_('Message'),
                           widget=forms.Textarea(attrs={'class': 'pretty_editor'}))

    hash = forms.CharField(label=_('Hash'),
                           widget=forms.HiddenInput())

    class Meta(object):
        model = Post
        fields = ('body',)

    def __init__(self, *args, **kwargs):
        if args:
            kwargs.update(dict(zip(inspect.getargspec(super(PostForm, self).__init__)[0][1:], args)))

        self.user = kwargs.pop('user', None)
        self.ip = kwargs.pop('ip', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        self.actor = kwargs.pop('actor', None)
        self.pollformset = None

            #Handle topic subject, poll type and question if editing topic head
        if ('instance' in kwargs) and kwargs['instance'] and (kwargs['instance'].topic.head == kwargs['instance']):
            kwargs.setdefault('initial', {})['name'] = kwargs['instance'].topic.name

            if kwargs['instance'].topic.poll and not defaults.PYBB_DISABLE_POLLS:
                kwargs.setdefault('initial', {})['poll_type'] = kwargs['instance'].topic.poll.type
                kwargs.setdefault('initial', {})['poll_question'] = kwargs['instance'].topic.poll.question

        super(PostForm, self).__init__(**kwargs)

        self.fields['hash'].initial = self.instance.get_hash()

        if not defaults.PYBB_DISABLE_POLLS:
            self.fields['poll_type'] = forms.TypedChoiceField(label=_('Poll type'),
                                                              choices=Poll.TYPE_CHOICES,
                                                              coerce=int,
                                                              initial=Poll.TYPE_NONE)
            self.fields['poll_question'] = forms.CharField(label=_('Poll question'),
                                                           required=False,
                                                           widget=forms.Textarea(attrs={'class': 'no-markitup'}))

        if not (self.forum or self.topic or self.instance.pk):
            self.fields['forum'] = forms.ModelChoiceField(label=_('Forum'),
                                                          queryset=Forum.objects.all().order_by('name'),
                                                          required=True)

        # remove topic specific fields
        if not (self.forum or (self.instance.pk and (self.instance.topic.head == self.instance))):

            if (self.instance.pk and not self.instance.topic.head == self.instance) or self.topic:
                del self.fields['name']

            if not defaults.PYBB_DISABLE_POLLS:
                del self.fields['poll_type']
                del self.fields['poll_question']

    def clean_name(self):
        name = self.cleaned_data['name']

        if self.topic:
            return name

        if not defaults.PYBB_DUPLICATE_TOPIC_SLUG_ALLOWED:
            try:
                Topic.objects.get(slug=slugify(name), forum=self.forum)
            except Topic.DoesNotExist:
                return name
            raise forms.ValidationError(self.error_messages['duplicate'])

        return name

    def clean_body(self):
        body = self.cleaned_data['body']
        user = self.user or self.instance.user
        if defaults.PYBB_BODY_VALIDATOR:
            defaults.PYBB_BODY_VALIDATOR(user, body)

        for cleaner_class in defaults.PYBB_BODY_CLEANERS:
            body = load_class(cleaner_class)(user, body)
        return body

    def is_valid(self):
        is_valid = super(PostForm, self).is_valid()

        if self.pollformset:
            is_valid &= self.pollformset.is_valid()

        return is_valid

    def clean(self):
        if not defaults.PYBB_DISABLE_POLLS:
            poll_type = self.cleaned_data.get('poll_type', None)
            poll_question = self.cleaned_data.get('poll_question', None)
            if poll_type is not None and poll_type != Poll.TYPE_NONE and not poll_question:
                raise forms.ValidationError(_('Poll''s question is required when adding a poll'))

        return self.cleaned_data

    def save(self, commit=True):
        if self.instance.pk:
            post = super(PostForm, self).save(commit=False)
            if self.user:
                post.user = self.user

            if self.actor and post.user_id == self.actor.pk:
                if post.is_updatable():
                    post.updated = tznow()

            if post.topic.head == post:
                topic = post.topic

                topic.name = self.cleaned_data['name']
                topic.updated = tznow()
                topic.save()

                if not defaults.PYBB_DISABLE_POLLS:
                    if self.cleaned_data['poll_type'] != Poll.TYPE_NONE:
                        poll = topic.poll or Poll()
                        poll.type = self.cleaned_data['poll_type']
                        poll.question = self.cleaned_data['poll_question']

                        is_new = poll.pk is None

                        poll.save()

                        if is_new:
                            topic.poll = poll
                            topic.save()
                    else:
                        if topic.poll:
                            topic.poll.answers.all().delete()
                            topic.poll = None
                            topic.save()

            post.save()

            return post

        allow_post = True

        if defaults.PYBB_PREMODERATION:
            allow_post = defaults.PYBB_PREMODERATION(self.user, self.cleaned_data['body'])

        if 'forum' in self.cleaned_data and not self.forum:
            self.forum = self.cleaned_data['forum']

        if self.forum:
            topic = Topic(
                forum=self.forum,
                user=self.user,
                name=self.cleaned_data['name'],
            )

            if not allow_post:
                topic.on_moderation = True
            topic.save()

            if not defaults.PYBB_DISABLE_POLLS:
                if 'poll_type' in self.cleaned_data and self.cleaned_data['poll_type'] != Poll.TYPE_NONE:
                    poll = Poll(
                        type=self.cleaned_data['poll_type'],
                        question=self.cleaned_data['poll_question']
                    )
                    poll.save()

                    topic.poll = poll
        else:
            topic = self.topic

        post = Post(topic=topic, user=self.user, user_ip=self.ip,
                    body=self.cleaned_data['body'], hash=self.cleaned_data['hash'])

        if not allow_post:
            post.on_moderation = True

        post.save()

        return post


class AdminPostForm(PostForm):
    """
    Superusers can post messages from any user and from any time
    If no user with specified name - new user will be created
    """
    login = forms.ModelChoiceField(label=_('User'), queryset=User.objects.all())

    def __init__(self, *args, **kwargs):
        if args:
            kwargs.update(dict(zip(inspect.getargspec(forms.ModelForm.__init__)[0][1:], args)))

        super(AdminPostForm, self).__init__(**kwargs)

    def save(self, *args, **kwargs):
        self.user = self.cleaned_data['login']

        return super(AdminPostForm, self).save(*args, **kwargs)


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False, label='')

    def filter(self, qs):
        if self.is_valid():
            query = self.cleaned_data['query']
            return qs.filter(username__contains=query)

        return qs


class PollForm(forms.Form):
    def __init__(self, poll, *args, **kwargs):
        self.poll = poll

        super(PollForm, self).__init__(*args, **kwargs)

        qs = PollAnswer.objects.filter(poll=poll)

        if poll.type == Poll.TYPE_SINGLE:
            self.fields['answers'] = forms.ModelChoiceField(
                label='', queryset=qs, empty_label=None,
                widget=forms.RadioSelect())
        elif poll.type == Poll.TYPE_MULTIPLE:
            self.fields['answers'] = forms.ModelMultipleChoiceField(
                label='', queryset=qs,
                widget=forms.CheckboxSelectMultiple())

    def clean_answers(self):
        answers = self.cleaned_data['answers']

        if self.poll.type == Poll.TYPE_SINGLE:
            return [answers]

        return answers


class ForumForm(forms.ModelForm):
    error_messages = {
        'duplicate': _("A forum with that name already exists."),
    }

    class Meta:
        model = Forum
        exclude = ('moderators', 'updated', 'post_count',
                   'topic_count', 'readed_by', 'forum_count', 'last_topic',
                   'last_post')

    def clean_name(self):
        name = self.cleaned_data['name']

        try:
            qs = self._meta.model.objects.filter(slug=slugify(name))

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            qs.get()

        except self._meta.model.DoesNotExist:
            return name
        raise forms.ValidationError(self.error_messages['duplicate'])


class ModerationForm(forms.Form):
    def __init__(self, permissions, *args, **kwargs):
        self.obj = kwargs.pop('obj', None)
        self.user = kwargs.pop('user', None)

        super(ModerationForm, self).__init__(*args, **kwargs)

        self.permissions = permissions

        available_permissions = {}

        if self.user:
            if not self.obj:
                available_permissions = dict((permission.pk, permission)
                                             for permission in self.user.user_permissions.all())
            else:
                available_permissions = dict((permission.permission_id, permission)
                                             for permission in UserObjectPermission.objects.get_for_object(self.user, self.obj))

        for permission in self.permissions:
            initial = int(bool(permission.pk in available_permissions))

            self.fields[permission.codename] = forms.ChoiceField(label=permission.name,
                                                                 widget=forms.RadioSelect(),
                                                                 choices=(
                                                                     (0, _('No')),
                                                                     (1, _('Yes')),
                                                                 ), initial=initial)

    def save(self, user, obj=None):
        obj = obj or self.obj

        ctype = None

        if obj:
            ctype = ContentType.objects.get_for_model(obj)

        for permission in self.permissions:
            value = int(self.cleaned_data[permission.codename])

            if value:
                if obj:
                    UserObjectPermission.objects.assign_perm(permission.codename, user=user, obj=obj, ctype=ctype)
                else:
                    user.user_permissions.add(permission)
            else:
                if obj:
                    UserObjectPermission.objects.remove_perm(permission.codename, user=user, obj=obj, ctype=ctype)
                else:
                    user.user_permissions.remove(permission)


class SearchUserForm(forms.Form):
    username = forms.CharField(label=_('Username'), required=True)
    error_messages = {
        'unknown_username': _('A user with that username does not exist.'),
    }

    model_class = User

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            self.get_user(username)
        except self.model_class.DoesNotExist:
            raise forms.ValidationError(self.error_messages['unknown_username'])
        else:
            return username

    def get_user(self, username):
        return self.model_class.objects.get(username=username)


class PostsMoveExistingTopicForm(forms.Form):
    topic = forms.ModelChoiceField(label=_('Destination topic'),
                                   required=True,
                                   queryset=Topic.objects.visible())

    def __init__(self, *args, **kwargs):
        self.posts = kwargs.pop('posts', None)
        self.user = kwargs.pop('user', None)

        super(PostsMoveExistingTopicForm, self).__init__(*args, **kwargs)

    def save(self):
        topic = self.cleaned_data['topic']

        self.posts.update(topic=topic)
        topic.update_counters()

        return topic


class PostsMoveNewTopicForm(forms.Form):
    forum = forms.ModelChoiceField(label=_('Destination forum'),
                                   required=True,
                                   queryset=Forum.objects.all())

    name = forms.CharField(label=_('New name for this topic'),
                           required=True)

    error_messages = {
        'duplicate': _(u'A topic with the name "%(topic)s" already exists in the forum "%(forum)s"'),
    }

    def __init__(self, *args, **kwargs):
        self.posts = kwargs.pop('posts', None)
        self.user = kwargs.pop('user', None)

        super(PostsMoveNewTopicForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data

        if not defaults.PYBB_DUPLICATE_TOPIC_SLUG_ALLOWED:
            forum = self.cleaned_data['forum']

            name = self.cleaned_data['name']

            slug = slugify(name)

            try:
                forum.topics.get(slug=slug)
            except Topic.DoesNotExist:
                pass
            else:
                self._errors['name'] = self.error_class([self.error_messages['duplicate'] % {
                    'topic': name,
                    'forum': forum
                }])

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data

        topic = Topic.objects.create(forum=cleaned_data['forum'],
                                     name=cleaned_data['name'],
                                     user=self.user)

        self.posts.update(topic=topic)
        topic.update_counters()

        return topic


class TopicMoveForm(forms.Form):
    error_messages = {
        'duplicate': _(u'A topic with the name "%(topic)s" already exists in the forum "%(forum)s"'),
        'expired_not_empty': _(u'You must specify the expiring date')
    }

    name = forms.CharField(label=_('New name for this topic'),
                           required=False,
                           help_text='No required, only if you want to change the name of the topic')

    forum = forms.ModelChoiceField(label=_('Destination forum'),
                                   required=True,
                                   queryset=Forum.objects.all())

    redirection_type = forms.ChoiceField(label=_('Redirect'),
                                         choices=TopicRedirection.TYPE_CHOICES,
                                         widget=forms.RadioSelect,
                                         initial=TopicRedirection.TYPE_PERMANENT_REDIRECT)

    expired = forms.DateField(label=('Expires in'), required=False)

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.pop('topic', None)

        super(TopicMoveForm, self).__init__(*args, **kwargs)

        self.fields['forum'].initial = self.topic.forum

    def clean(self):
        cleaned_data = self.cleaned_data

        redirection_type = cleaned_data['redirection_type']

        if (int(redirection_type) == TopicRedirection.TYPE_EXPIRING_REDIRECT and
                (not 'expired' in cleaned_data or not cleaned_data['expired'])):
                self._errors['expired'] = self.error_class([self.error_messages['expired_not_empty']])

        if not defaults.PYBB_DUPLICATE_TOPIC_SLUG_ALLOWED:
            forum = self.cleaned_data['forum']

            if 'name' in self.cleaned_data and self.cleaned_data['name']:
                name = self.cleaned_data['name']

                slug = slugify(name)

                try:
                    forum.topics.get(slug=slug)
                except Topic.DoesNotExist:
                    pass
                else:
                    self._errors['name'] = self.error_class([self.error_messages['duplicate'] % {
                        'topic': name,
                        'forum': forum
                    }])
            else:
                try:
                    forum.topics.get(slug=self.topic.slug)
                except Topic.DoesNotExist:
                    pass
                else:
                    self._errors['name'] = self.error_class([self.error_messages['duplicate'] % {
                        'topic': self.topic,
                        'forum': forum
                    }])

        return cleaned_data

    def save(self):
        forum = self.cleaned_data['forum']

        topic = copy.copy(self.topic)
        topic.pk = None
        topic.forum = forum

        if self.cleaned_data['name']:
            topic.name = self.cleaned_data['name']

        topic.save()

        if ('expired' in self.cleaned_data and
                self.cleaned_data['redirection_type'] == TopicRedirection.TYPE_EXPIRING_REDIRECT):
            topic.absorb(self.topic,
                         redirection_type=self.cleaned_data['redirection_type'],
                         expired=self.cleaned_data['expired'])
        else:
            topic.absorb(self.topic,
                         redirection_type=self.cleaned_data['redirection_type'])

        self.topic.forum.update_counters()

        return topic


def get_topic_move_formset(topics, form=TopicMoveForm):
    class BaseTopicMoveFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            self.topics = topics

            super(BaseTopicMoveFormSet, self).__init__(*args, **kwargs)

        def _construct_form(self, i, **kwargs):
            kwargs['topic'] = self.topics[i]

            return super(BaseTopicMoveFormSet, self)._construct_form(i, **kwargs)

    return formset_factory(extra=len(topics), form=load_class(defaults.PYBB_TOPIC_MOVE_FORM), formset=BaseTopicMoveFormSet)


class TopicMergeForm(forms.Form):
    topic = forms.ModelChoiceField(label=_('Name of the topic'),
                                   help_text=_('Use this field to combine the current topic to another'),
                                   required=True,
                                   queryset=Topic.objects.visible())

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.pop('topic', None)

        super(TopicMergeForm, self).__init__(*args, **kwargs)

    def clean_topic(self):
        topic = self.cleaned_data['topic']

        if topic == self.topic:
            raise forms.ValidationError(_('You can\'t merge a topic in the same topic'))

        return topic

    def save(self):
        topic = self.cleaned_data['topic']

        topic.absorb(self.topic)

        return topic


def get_topic_merge_formset(topics, form=TopicMergeForm):
    class BaseTopicMergeFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            self.topics = topics

            super(BaseTopicMergeFormSet, self).__init__(*args, **kwargs)

        def _construct_form(self, i, **kwargs):
            kwargs['topic'] = self.topics[i]

            return super(BaseTopicMergeFormSet, self)._construct_form(i, **kwargs)

    return formset_factory(extra=len(topics), form=load_class(defaults.PYBB_TOPIC_MERGE_FORM), formset=BaseTopicMergeFormSet)


class TopicDeleteForm(forms.Form):
    confirm = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.pop('topic', None)

        super(TopicDeleteForm, self).__init__(*args, **kwargs)

    def save(self):
        if self.cleaned_data.get('confirm', True):
            if not self.topic.deleted:
                self.topic.mark_as_deleted()
            else:
                self.topic.mark_as_undeleted()

        return self.topic


def get_topic_delete_formset(topics, form=TopicDeleteForm):
    class BaseTopicDeleteFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            self.topics = topics

            super(BaseTopicDeleteFormSet, self).__init__(*args, **kwargs)

        def _construct_form(self, i, **kwargs):
            kwargs['topic'] = self.topics[i]

            return super(BaseTopicDeleteFormSet, self)._construct_form(i, **kwargs)

    return formset_factory(extra=len(topics), form=load_class(defaults.PYBB_TOPIC_DELETE_FORM), formset=BaseTopicDeleteFormSet)
