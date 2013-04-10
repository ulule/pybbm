from django.shortcuts import render_to_response
from django.http import Http404, QueryDict

from pure_pagination import Paginator, InvalidPage

from haystack.views import SearchView as BaseSearchView

from pybb.helpers import (lookup_users, lookup_post_topics,
                          lookup_post_attachments)
from pybb.contrib.search.fields import TreeModelMultipleChoiceField
from pybb.models import Forum


class SearchQuerySetSafeIterator(object):
    """
    Wrap a search queryset to prevent it to yield None. It only trips out
    the first None objects at the moment in __getitem__ and __len__. __iter__
    is completly safe.
    """
    def __init__(self,sqs):
        self.sqs = sqs
        self.offset = 0
        try:
            for ob in sqs:
                if ob is None:
                    self.offset +=1
                else:
                    break
        except ValueError:
            # a bug in haystack.query:122 : `if len(self) <= 0:`
            self.offset = 0
            self.sqs = []

    def __len__(self):
        len_ =  len(self.sqs) - self.offset
        if len_ >= 0:
            return len_
        # this must not happen
        return 0

    def count(self):
        return len(self)

    def _shift_slice(self, k, offset):
        if isinstance(k, slice):
            return slice(k.start + offset, k.stop + offset)
        else:
            return k + offset

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), \
                "Negative indexing is not supported."

        k = self._shift_slice(k, self.offset)

        result = self.sqs.__getitem__(k)
        if result is None:
            while result is None:
                k += 1
                result = self.sqs.__getitem__(k)
        elif isinstance(result,list):
            # TODO: replace striped results by consitent objects after the
            # original slice
            return [obj for obj in result if obj is not None]
        else:
            return result

    def __iter__(self):
        return self._iterator()

    def _iterator(self):
        for obj in self.sqs:
            if obj is not None:
                yield obj



class SearchView(BaseSearchView):
    def build_form(self, *args, **kwargs):
        '''
        Override to change the form and the searchqueryset according to the user.
        Be carefull this is not thread safe ! Use haystack.views.search_view_factory
        to build this view.
        '''
        form = super(SearchView, self).build_form(*args, **kwargs)

        user = self.request.user

        if not user.is_authenticated():
            form.searchqueryset = form.searchqueryset.exclude(hidden=True)
        elif not user.is_staff:
            form.searchqueryset = form.searchqueryset.exclude(staff=True)

        form.fields['forums'] = TreeModelMultipleChoiceField(
            queryset=Forum.objects.filter_by_user(user),
            join_field='forum_id',
            required=False
        )

        return form

    def build_page(self):
        """
        override to use pure_pagination
        """
        try:
            page_no = int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            raise Http404("Not a valid number for page.")

        if page_no < 1:
            raise Http404("Pages should be 1 or greater.")

        start_offset = (page_no - 1) * self.results_per_page

        self.results[start_offset:start_offset + self.results_per_page]
        it = SearchQuerySetSafeIterator(self.results)

        paginator = Paginator(it, self.results_per_page)

        try:
            page = paginator.page(page_no)
        except InvalidPage:
            raise Http404("No such page!")

        return (paginator, page)

    def normalize_results(self, result_list):
        """
        Adapt results to Post interface in order to display them the same way
        in templates
        """
        lookup_post_topics(result_list)
        lookup_users(result_list)
        lookup_post_attachments(result_list)

        for result in result_list:
            result.id = result.pk
            result.get_body_html = False
            result.get_attachments = result._attachments

    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.
        """
        (paginator, page) = self.build_page()

        # build query_string
        query_dict = self.form.data.copy()

        if not isinstance(query_dict, QueryDict):
            ## no querystring (e.g. /search/ )
            qs = ''
        else:
            try:
                del query_dict['page']
            except KeyError:
                pass
            qs = query_dict.urlencode()

        # is it an advanced search
        advanced = False
        for arg in ('forums', 'user', 'replies_limit',
                    'search_topic_name', 'start_date', 'end_date',
                    'with_attachment', ):
            if self.form.data.get(arg, None):
                advanced = True
                break

        self.normalize_results(page.object_list)

        # Fake Page object to build posts redirect_url
        post_page = {
            'number': 1
        }

        context = {
            'only_topics': self.form.data.get('search_topic_name', False),
            'qs': qs,
            'query': self.query,
            'form': self.form,
            'page_obj': page,
            'paginator': paginator,
            'suggestion': None,
            'is_paginated': paginator.num_pages > 1,
            'show_information': True,
            'post_page': post_page,
            'advanced': advanced,
        }

        if (self.results.__len__() > 0 and hasattr(self.results, 'query') and
                self.results.query.backend.include_spelling):
            context['suggestion'] = self.form.get_suggestion()

        context.update(self.extra_context())

        return render_to_response(self.template,
                                  context,
                                  context_instance=self.context_class(self.request))
