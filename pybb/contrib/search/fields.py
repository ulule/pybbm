from itertools import chain

from django.forms.widgets import SelectMultiple
from django.forms import ModelMultipleChoiceField
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe


class TreeSelectMultiple(SelectMultiple):
    """
    A SelectMultiple widget that takes a treee of objects as a tuple or list of the form::
        (
            (root_val,('root_label',(
                branch1_val,('branch1_label',
                    (leaf11_val,'leaf11_label')
                    (leaf12_val,'leaf12-label')
                )
            ))
        ))
    """

    def render_option(self, selected_choices, option_value, option_label, level):
        # webkit workaround. options are not stylable
        indent = mark_safe('&nbsp;' * 3 * level)
        option_value = force_unicode(option_value)
        level_html = u' class="opt-tree-level%s"' % level
        if option_value in selected_choices:
            selected_html = u' selected="selected"'
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        option_label = mark_safe('%s%s' % (indent, option_label))
        return u'<option value="%s"%s%s>%s</option>' % (
            escape(option_value), selected_html, level_html,
            conditional_escape(force_unicode(option_label)))

    def render_options(self, choices, selected_choices, level=0):
        if not choices:
            choices = tuple(chain(self.choices, choices))
        # Normalize to strings.
        selected_choices = set(force_unicode(v) for v in selected_choices)
        output = []
        for option_value, option_label in choices:
            if isinstance(option_label, (list, tuple)):
                label = option_label[0]
                output.append(self.render_option(selected_choices, option_value, label, level))
                output.append(self.render_options(option_label[1:], selected_choices, level=level + 1))
            else:
                output.append(self.render_option(selected_choices, option_value, option_label, level))
        return u'\n'.join(output)


class TreeModelMultipleChoiceField(ModelMultipleChoiceField):
    """
    A model multi choice field that is aware of objects hierarchy. The tree is built using
    `join_field` to get the relatoin between a child and its parent. It works only on a
    single model.
    """
    widget = TreeSelectMultiple

    def __init__(self, queryset, join_field="parent", cache_choices=False, required=True,
                 widget=None, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        self.join_field = join_field
        self.to_field_name = None

        super(TreeModelMultipleChoiceField, self).__init__(queryset,
                                                           cache_choices, required, widget, label, initial,
                                                           help_text, *args, **kwargs)

    def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, '_choices'):
            return self._choices

        object_list = list(self.queryset)
        result = []
        object_ids = [o.id for o in object_list]
        for root in object_list:
            if not getattr(root, self.join_field) or root.id not in object_ids:
                result.append(self._build_obj_branch(root, object_list))
        return result

    choices = property(_get_choices, ModelMultipleChoiceField._set_choices)

    def _build_obj_branch(self, obj, objs):
        leaf_objs = [l for l in objs if getattr(l, self.join_field) == obj.pk]
        if not len(leaf_objs):
            return (self.prepare_value(obj), mark_safe(self.label_from_instance(obj)))
        leaves = [mark_safe(self.label_from_instance(obj))]
        for leaf in leaf_objs:
            leaves.append(self._build_obj_branch(leaf, objs))
        return (self.prepare_value(obj), leaves)
