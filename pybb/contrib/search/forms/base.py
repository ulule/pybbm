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

    search_sub_forums = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['search_sub_forums'].initial = True

        self.fields['forums'] = TreeModelMultipleChoiceField(queryset=Forum.objects.all(),
                                                             join_field='forum_id',
                                                             required=False)


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

        # sub_forum search
        forums = self.cleaned_data.get('forums', None)
        if forums:
            if not self.cleaned_data.get('search_sub_forums', True):
                sqs = sqs.filter(forum_id__in=[f.id for f in forums])
            else:
                sqs = sqs.filter(topic_breadcrumbs__in=[f.id for f in forums])

        if self.cleaned_data.get('user_id', None):
            sqs = sqs.filter(user_id=self.cleaned_data['user'].pk)
        if self.cleaned_data.get('replies', None):
            sqs = sqs.filter(replies__gte=self.cleaned_data['replies'])
        if self.cleaned_data.get('topic_id', None):
            sqs = sqs.filter(topic_id=self.cleaned_data['topic_id'])

        return sqs
