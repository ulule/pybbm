from django import template

from pybb.contrib.reports.models import Report

register = template.Library()


class ReportCountNode(template.Node):
    model = Report

    def __init__(self, filters, context_var):
        self.context_var = context_var
        self.filters = filters

    def render(self, context):
        result = self.model.objects.filter(**self.filters).count()

        context[self.context_var] = result

        return ''


@register.tag
def get_new_report_count(parser, token):
    bits = token.split_contents()

    format = '{% get_new_report_count as context_var %}'

    if len(bits) != 3 or bits[1] != 'as':
        raise template.TemplateSyntaxError("get_new_report_count tag should be in format: %s" % format)

    context_var = bits[2]

    return ReportCountNode({
        'status': Report.STATUS_NEW
    }, context_var)
