import urllib
import urlparse

from django import template

register = template.Library()

@register.filter(name='any')
def any_(value):
    return bool(value) and any(value)

@register.filter
def contains_comma(value):
    return isinstance(value, basestring) and ', ' in value

@register.filter(name='contains')
def contains_(value, arg):
    return arg in value

@register.simple_tag(takes_context=True)
def updated_query_string(context, **kwargs):
    query_params = urlparse.parse_qs(context['request'].META['QUERY_STRING'])

    for k, v in kwargs.items():
        if not v:
            query_params.pop(k, None)
        else:
            query_params[k] = [v]

    new_query_string = urllib.urlencode(query_params, doseq=True)

    return ('?' + new_query_string) if new_query_string else context['request'].path
