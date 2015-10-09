from __future__ import unicode_literals

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.utils.encoding import iri_to_uri


FONT_SIZES = {
    '1': '0.77em',
    '3': '1.23em',
    '4': '1.38em',
    '5': '1.86em',
    '6': '2.46em',
    '7': '3.69em',
}

FONT_FAMILIES = {
    'Arial': "'Arial'",
    'Arial Black': "'Arial Black'",
    'Comic Sans MS': "'Comic Sans MS'",
    'Courier New': "'Courier New'",
    'Georgia': "'Georgia'",
    'Impact': "'Impact'",
    'Sans-serif': "'Sans-serif'",
    'Serif': "'Serif'",
    'Times New Roman': "'Times New Roman'",
    'Trebuchet MS': "'Trebuchet MS'",
    'Verdana': "'Verdana'",
}


def url(tag_name, value, options, parent, context):
    if 'url' not in options:
        options['url'] = value

    str_href = iri_to_uri(options['url'])

    attrs = ['%s="%s"' % (attr, options[attr])
             for attr in ('title', 'class',) if attr in options]

    attrs += [
        'target="_blank"',
        'rel="nofollow"'
    ]

    result = '<a href="%(str_href)s"%(attrs)s>%(text)s</a>' % {
        'str_href': str_href,
        'text': value,
        'attrs': ' ' + ' '.join(attrs) if len(attrs) else ''
    }

    return result


def img(tag_name, value, options, parent, context):
    str_src = iri_to_uri(value)

    attrs = ['%s="%s"' % (attr, options[attr])
             for attr in ('title', 'class', 'alt',) if attr in options]

    # the 'alt' attribute is required
    if 'alt' not in options:
        attrs.append('alt=""')

    return '<img src="%(str_src)s"%(attrs)s />' % {
        'str_src': str_src,
        'attrs': ' ' + ' '.join(attrs) if len(attrs) else ''
    }


def spoiler(tag_name, value, options, parent, context):
    return '<div class="spoiler-container"><strong>%s</strong><input class="btn-mini spoiler-trigger" type="button" value="%s" /><div class="spoiler">%s</div></div>' % (_('Spoiler!'), _('Show Spoiler'), value)


def font_size(tag_name, value, options, parent, context):
    if 'size' in options and options['size'] in FONT_SIZES:
        return '<span style="font-size:%s">%s</span>' % (FONT_SIZES[options['size']], value)

    # for [size=2]..[/size] we don't want formatting (font-size would be 1em)
    # as for any other value
    return value


def font_family(tag_name, value, options, parent, context):
    if 'font' in options and options['font'] in FONT_FAMILIES:
        return '<span style="font-family:%s">%s</span>' % (FONT_FAMILIES[options['font']], value)
    # we don't want formatting for any other value
    return value


def email(tag_name, value, options, parent, context):
    if 'email' in options:
        try:
            validate_email(options['email'])
            return '<a href="mailto:%s">%s</a>' % (options['email'], value)
        except ValidationError:
            pass
    # we don't want formatting if there's no email or the email doesn't validate
    return value
