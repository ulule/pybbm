from django.test import TransactionTestCase
from django.core.urlresolvers import reverse

from pybb.tests.base import SharedTestModule
from pybb.contrib.quotes.models import Quote

from pybb.models import Post


class ReportsTest(TransactionTestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()

    def test_simple_quote(self):
        post = Post(user=self.staff, body='[quote="zeus;%d"]Super quote[/quote]' % self.post.pk, topic=self.topic)
        post.save()

        self.assertEqual(post.body_html, u'<blockquote>    <div class="quote-author">        Posted by <a class="quote-author-name" href="/users/zeus/">zeus</a>        <a class="quote-message-link" href="/xfoo/1-etopic-1/#post1" rel="nofollow"></a>    </div>    <div class="quote-message">        Super quote    </div></blockquote>')

        self.assertEqual(Quote.objects.filter(from_post=post).count(), 1)

    def test_double_quote(self):
        post = Post(user=self.staff, body='[quote="%s;%d"]%s[/quote]' % (self.post.user.username,
                                                                         self.post.pk,
                                                                         self.post.body),
                    topic=self.topic)
        post.save()

        post = Post(user=self.superuser, body='[quote="%s;%d"]%s[/quote]' % (post.user.username,
                                                                             post.pk,
                                                                             post.body), topic=self.topic)
        post.save()

        self.assertEqual(post.body_html, u'<blockquote>    <div class="quote-author">        Posted by <a class="quote-author-name" href="/users/thoas/">thoas</a>        <a class="quote-message-link" href="/xfoo/1-etopic-1/#post2" rel="nofollow"></a>    </div>    <div class="quote-message">        <blockquote>    <div class="quote-author">        Posted by <a class="quote-author-name" href="/users/zeus/">zeus</a>        <a class="quote-message-link" href="/xfoo/1-etopic-1/#post1" rel="nofollow"></a>    </div>    <div class="quote-message">        bbcode <strong>test</strong>    </div></blockquote>    </div></blockquote>')

        self.assertEqual(Quote.objects.filter(from_post=post).count(), 2)

    def test_multiple_quote_add(self):
        self.login_client(username='thoas', password='$ecret')

        post = Post(topic=self.topic, user=self.superuser, body='[b]do you want my pere nowel?[/b]')
        post.save()

        response = self.client.post(reverse('quote'), data={
            'topic_id': self.topic.pk,
            'post_id': post.pk
        })

        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('pybb:post_create',
                                           kwargs={'topic_id': self.topic.id}) + '?quote_id=%d' % self.post.id)
        self.assertEqual(response.context['form'].initial['body'], u'[quote="zeus;1"]bbcode [b]test[/b][/quote]\n\n[quote="oleiade;2"][b]do you want my pere nowel?[/b][/quote]\n')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('quote'), data={
            'topic_id': self.topic.pk,
            'post_id': post.pk
        })

        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('pybb:post_create',
                                           kwargs={'topic_id': self.topic.id}))
        self.assertTrue(not 'body' in response.context['form'].initial)
        self.assertEqual(response.status_code, 200)
