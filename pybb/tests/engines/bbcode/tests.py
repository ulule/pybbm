from pybb.tests.base import TestCase
from pybb.engines.bbcode import BBCodeMarkupEngine
from pybb.engines.bbcode.formatters import FONT_FAMILIES, FONT_SIZES

from pybb.models.base import markup


class BBCodeMarkupEngineTest(TestCase):
    def test_simple_formatters(self):
        messages = (
            ('[left]test[/left]', '<div style="text-align:left;">test</div>'),
            ('[center]test[/center]', '<div style="text-align:center;">test</div>'),
            ('[right]test[/right]', '<div style="text-align:right;">test</div>'),
            ('[ul][li]one[/li][li]two[/li][li]three[/li][/ul]', '<ul><li>one</li><li>two</li><li>three</li></ul>'),
            ('[ol][li]one[/li][li]two[/li][li]three[/li][/ol]', '<ol><li>one</li><li>two</li><li>three</li></ol>'),
            ('[url url=http://ulule.com]ulule[/url]', '<a href="http://ulule.com" target="_blank" rel="nofollow">ulule</a>'),
            ('[url url="http://ulule.com" title="Ulule"]ulule[/url]', '<a href="http://ulule.com" title="Ulule" target="_blank" rel="nofollow">ulule</a>'),
            ('[url url="http://ulule.com" title="Ulule" class="link"]ulule[/url]', '<a href="http://ulule.com" title="Ulule" class="link" target="_blank" rel="nofollow">ulule</a>'),
            ('[img]http://ulule.com/logo.png[/img]', '<img src="http://ulule.com/logo.png" alt="" />'),
            ('[img alt="Ulule"]http://ulule.com/logo.png[/img]', '<img src="http://ulule.com/logo.png" alt="Ulule" />'),
            ('[img class="link"]http://ulule.com/logo.png[/img]', '<img src="http://ulule.com/logo.png" class="link" alt="" />'),
            ('[img alt="Ulule" class="link"]http://ulule.com/logo.png[/img]', '<img src="http://ulule.com/logo.png" class="link" alt="Ulule" />'),
            ('[email email="florent@ulule.com"]florent[/email]', '<a href="mailto:florent@ulule.com">florent</a>'),
            ('[youtube]_UE7C3sQHWs[/youtube]', '<iframe width="560" height="315" frameborder="0" src="http://www.youtube.com/embed/_UE7C3sQHWs?wmode=opaque" data-youtube-id="_UE7C3sQHWs" allowfullscreen=""></iframe>'),
        )

        for bbcode, result in messages:
            markup_engine = BBCodeMarkupEngine(bbcode)
            self.assertEqual(markup_engine.render(), result)

        for label, family in FONT_FAMILIES.iteritems():
            markup_engine = BBCodeMarkupEngine('[font font=%s]test[/font]' % label)
            self.assertEqual(markup_engine.render(), '<span style="font-family:%s">test</span>' % family)

        for label, size in FONT_SIZES.iteritems():
            markup_engine = BBCodeMarkupEngine('[size size=%s]test[/font]' % label)
            self.assertEqual(markup_engine.render(), '<span style="font-size:%s">test</span>' % size)

    def test_multiple_formatters(self):
        self.staff

        messages = (
            ('[left][url url="http://ulule.com" title="Ulule"][img alt="Ulule" class="link"]http://ulule.com/logo.png[/img][/url][/left]',
             u'<div style="text-align: left;"><a rel="nofollow" title="Ulule" target="_blank" href="http://ulule.com"><img src="http://ulule.com/logo.png" alt="Ulule" class="link"></a></div>'),
            ('[left]@thoas[/left]',
             u'<div style="text-align: left;">@<a class="mention" href="/users/thoas/">thoas</a></div>'),
            ('[left]@thoas [url url="http://ulule.com" title="Ulule"][img alt="Ulule" class="link"]http://ulule.com/logo.png[/img][/url][/left]',
             u'<div style="text-align: left;">@<a class="mention" href="/users/thoas/">thoas</a> <a rel="nofollow" title="Ulule" target="_blank" href="http://ulule.com"><img src="http://ulule.com/logo.png" alt="Ulule" class="link"></a></div>'),
        )

        for bbcode, result in messages:
            mark = markup(bbcode, obj=self.post)

            self.assertHTMLEqual(mark, result)
