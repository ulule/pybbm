import datetime

from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from haystack.forms import SearchForm as HaystackSearchForm
from haystack.inputs import AutoQuery

from pybb.contrib.search.fields import TreeModelMultipleChoiceField
from pybb.models import Forum


class SearchForm(HaystackSearchForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(),
                                  required=False,
                                  label=_('Username'))

    replies = forms.IntegerField(label=_('Number of answers'),
                                 min_value=0, required=False)

    search_topic_name = forms.BooleanField(required=False)
    with_attachment = forms.BooleanField(required=False)

    start_date = forms.DateTimeField(required=False)
    end_date = forms.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        self.fields['forums'] = TreeModelMultipleChoiceField(queryset=Forum.objects.all(),
                                                             join_field='forum_id',
                                                             required=False)

    def clean(self):
        data = super(HaystackSearchForm, self).clean()
        if data.get('start_date', None):
            if not data.get('end_date', None):
                data['end_date']= datetime.datetime.now()
            if data['start_date'] > data['end_date']:
                raise forms.ValidationError('Start date is after end date')
        return data

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        # topic name search
        if self.cleaned_data.get('search_topic_name', False):
            sqs = self.searchqueryset.filter(
                topic_name=AutoQuery(self.cleaned_data['q']))
            sqs = sqs.filter(is_first_post = True)
        else:
            sqs = super(SearchForm, self).search()

        sqs = sqs.order_by('-created')

        forums = self.cleaned_data.get('forums', None)
        if forums:
            sqs = sqs.filter(topic_breadcrumbs__in=[f.id for f in forums])
        if self.cleaned_data.get('user_id', None):
            sqs = sqs.filter(user_id=self.cleaned_data['user'].pk)
        if self.cleaned_data.get('replies', None):
            sqs = sqs.filter(replies__gte=self.cleaned_data['replies'])
        if self.cleaned_data.get('topic_id', None):
            sqs = sqs.filter(topic_id=self.cleaned_data['topic_id'])
        if self.cleaned_data.get('start_date',None):
            sqs = sqs.filter(updated__gte=self.cleaned_data['start_date'])
        if self.cleaned_data.get('end_date',None):
            sqs = sqs.filter(updated__lte=self.cleaned_data['end_date'])
        if self.cleaned_data.get('with_attachment', None):
            sqs = sqs.filter(has_attachment=self.cleaned_data['with_attachment'])

        return sqs
