from django.shortcuts import render_to_response
from django.http import Http404, QueryDict

from pure_pagination import Paginator, InvalidPage

from haystack.views import SearchView as BaseSearchView

from pybb.helpers import (lookup_users, lookup_post_topics,
                          lookup_post_attachments)
from pybb.contrib.search.fields import TreeModelMultipleChoiceField
from pybb.contrib.search.utils import SearchQuerySetSafeIterator
from pybb.models import Forum


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
