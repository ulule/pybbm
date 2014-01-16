from django.core.urlresolvers import reverse

from pybb.tests.base import TestCase, get_uploaded_file
from pybb import defaults
from pybb.models import Post, Attachment


class AttachmentTest(TestCase):
    def setUp(self):
        self.PYBB_ATTACHMENT_ENABLE = defaults.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_ATTACHMENT_ENABLE = True
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = False

    def test_attachment(self):
        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        self.login()
        response = self.client.get(post_create_url)
        values = self.get_form_values(response)
        values['body'] = 'test attachment'
        values['attachments-0-file'] = get_uploaded_file('attachment.png')
        response = self.client.post(post_create_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(body='test attachment').exists())

    def test_attachment_complete(self):
        post_create_url = reverse('pybb:post_create', kwargs={'topic_id': self.topic.id})
        self.login()
        response = self.client.get(post_create_url)
        values = self.get_form_values(response)

        post_attachment_url = reverse('pybb:attachment_list')

        response = self.client.post(post_attachment_url, data={
            'post_hash': values['hash']
        })

        self.assertEqual(response.status_code, 200)

        attachment_values = self.get_form_values(response, form='attachments-form', attr='//form[@id="%s"]')

        attachment_values['attachments-0-file'] = get_uploaded_file('attachment.png')

        response = self.client.post(post_attachment_url, attachment_values)

        self.assertEqual(Attachment.objects.filter(post_hash=values['hash']).count(), 1)

        values['body'] = 'test attachment'

        response = self.client.post(post_create_url, values)

        self.assertEqual(response.status_code, 302)

        post = Post.objects.get(hash=values['hash'])

        self.assertEqual(Attachment.objects.filter(post=post).count(), 1)

    def test_attachment_delete_view(self):
        self.post.hash = self.post.get_hash()
        self.post.save()

        file = get_uploaded_file('attachment.png')

        attachment = Attachment.objects.create(
            file=file,
            post_hash=self.post.hash,
            post=self.post,
            user=self.user
        )

        self.login()

        response = self.client.get(reverse('pybb:attachment_delete', kwargs={
            'pk': attachment.pk
        }))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'pybb/attachment/delete.html')

    def test_attachment_delete_complete(self):
        self.post.hash = self.post.get_hash()
        self.post.save()

        file = get_uploaded_file('attachment.png')

        attachment = Attachment.objects.create(
            file=file,
            post_hash=self.post.hash,
            post=self.post,
            user=self.user
        )

        self.login()

        response = self.client.post(reverse('pybb:attachment_delete', kwargs={
            'pk': attachment.pk
        }))

        self.assertRedirects(response, self.post.get_absolute_url())

        self.assertRaises(Attachment.DoesNotExist, lambda: Attachment.objects.get(pk=attachment.pk))

    def test_attachment_update_view(self):
        self.post.hash = self.post.get_hash()
        self.post.save()

        file = get_uploaded_file('attachment.png')

        attachment = Attachment.objects.create(
            file=file,
            post_hash=self.post.hash,
            post=self.post,
            user=self.user
        )

        self.login()

        post_attachment_url = reverse('pybb:attachment_list')

        response = self.client.post(post_attachment_url, data={
            'post_hash': self.post.hash
        })

        self.assertEqual(response.status_code, 200)

        self.assertEqual(list(response.context['attachments']), [attachment])

    def test_attachment_update_complete(self):
        self.post.hash = self.post.get_hash()
        self.post.save()

        file = get_uploaded_file('attachment.png')

        Attachment.objects.create(
            file=file,
            post_hash=self.post.hash,
            post=self.post,
            user=self.user
        )

        self.login()

        post_attachment_url = reverse('pybb:attachment_list')

        response = self.client.post(post_attachment_url, data={
            'post_hash': self.post.hash
        })

        attachment_values = self.get_form_values(response, form='attachments-form', attr='//form[@id="%s"]')

        attachment_values['attachments-0-file'] = get_uploaded_file('attachment.png')

        self.assertEqual(response.status_code, 200)

        response = self.client.post(post_attachment_url, data=attachment_values)

        self.assertEqual(Attachment.objects.filter(post=self.post).count(), 2)

    def tearDown(self):
        defaults.PYBB_ATTACHMENT_ENABLE = self.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION
