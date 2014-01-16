from django.core.urlresolvers import reverse
from django.template import Context, Template

from pybb.tests.base import TestCase

from .forms import ReportMessageForm
from .models import Report, ReportMessage


class ReportsTest(TestCase):
    def test_report_create_view(self):
        url = reverse('report_create', args=[self.post.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.login_as(self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response,
                                'pybb/report/create.html')

        self.failUnless(isinstance(response.context['form'],
                                   ReportMessageForm))

    def test_report_create_complete(self):
        url = reverse('report_create', args=[self.post.pk])

        self.login_as(self.staff)

        response = self.client.post(url, data={
            'message': 'This post is not right'
        })

        self.assertRedirects(response,
                             self.post.topic.get_absolute_url())

        self.assertEqual(Report.objects.filter(post=self.post).count(), 1)

        report = Report.objects.get(post=self.post)

        self.assertEqual(report.message_count, 1)

        self.assertEqual(ReportMessage.objects.filter(report__post=self.post).count(), 1)

    def test_report_create_complete_with_existing_report(self):
        url = reverse('report_create', args=[self.post.pk])

        self.login_as(self.superuser)

        report = Report.objects.create(post=self.post)
        ReportMessage.objects.create(report=report, message='test', user=self.staff)

        response = self.client.post(url, data={
            'message': 'This post is not right again'
        })

        self.assertRedirects(response,
                             self.post.topic.get_absolute_url())

        self.assertEqual(Report.objects.filter(post=self.post).count(), 1)

        self.assertEqual(Report.objects.get(pk=report.pk).message_count, 2)

        self.assertEqual(ReportMessage.objects.filter(report__post=self.post).count(), 2)

    def test_double_report(self):
        url = reverse('report_create', args=[self.post.pk])

        report = Report.objects.create(post=self.post)
        ReportMessage.objects.create(report=report, message='test', user=self.staff)

        self.login_as(self.staff)

        response = self.client.post(url, data={
            'message': 'This post is not right again'
        })

        self.assertRedirects(response,
                             self.post.topic.get_absolute_url())

        self.assertEqual(Report.objects.get(pk=report.pk).message_count, 1)

        self.assertEqual(ReportMessage.objects.filter(report__post=self.post).count(), 1)

    def test_report_list_view(self):
        url = reverse('report_list')

        self.login_as(self.staff)

        report = Report.objects.create(post=self.post)
        ReportMessage.objects.create(report=report, message='test', user=self.staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(list(response.context['report_list']), [report])
        self.assertTemplateUsed(response,
                                'pybb/report/list.html')

    def test_report_detail_view(self):
        self.login_as(self.staff)

        report = Report.objects.create(post=self.post)
        ReportMessage.objects.create(report=report, message='test', user=self.staff)

        response = self.client.get(report.get_absolute_url())

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response,
                                'pybb/report/detail.html')

    def test_report_close_view(self):
        self.login_as(self.staff)

        report = Report.objects.create(post=self.post)
        ReportMessage.objects.create(report=report, message='test', user=self.staff)

        response = self.client.get(reverse('report_close', args=[report.pk]))

        self.assertRedirects(response,
                             reverse('report_list'))

        report = Report.objects.get(pk=report.pk)

        self.assertTrue(report.is_status_closed())

    def test_get_new_report_count_templatetags(self):
        Report.objects.create(post=self.post)

        t = Template("{% load report_tags %}{% get_new_report_count as report_count %}{{ report_count }}")
        c = Context()
        self.failUnlessEqual(u'1', t.render(c))
