# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

PYBB_QUOTES_USER_URL = getattr(settings, 'PYBB_QUOTES_USER_URL',
                               lambda user: reverse('user_detail', args=[user.username]))

PYBB_QUOTES_POST_URL = getattr(settings, 'PYBB_QUOTES_POST_URL',
                               lambda post: post.get_absolute_url())

PYBB_QUOTES_MAX_DEPTH = getattr(settings, 'PYBB_QUOTES_MAX_DEPTH', -1)

PYBB_QUOTES_QUOTE_VALID_FORMAT = getattr(settings, 'PYBB_QUOTES_QUOTE_VALID_FORMAT', _(u"""<blockquote>\
    <div class="quote-author">\
        Posted by <a href="%(user_url)s" class="quote-author-name">%(username)s</a>\
        <a href="%(post_url)s" rel="nofollow" class="quote-message-link"></a>\
    </div>\
    <div class="quote-message">\
        %(message)s\
    </div>\
</blockquote>"""))


PYBB_QUOTES_QUOTE_MINIMAL_FORMAT = getattr(settings, 'PYBB_QUOTES_QUOTE_MINIMAL_FORMAT', _(u"""<blockquote>\
    <div class="quote-author">\
        Posted by <span class="quote-author-name">%(username)s</span>\
    </div>\
    <div class="quote-message">\
        %(message)s\
    </div>\
</blockquote>"""))

PYBB_QUOTES_QUOTE_BASIC_FORMAT = getattr(settings, 'PYBB_QUOTES_QUOTE_BASIC_FORMAT', _(u"""<blockquote>\
    <div class="quote-message">\
        %(message)s\
    </div>\
</blockquote>"""))
