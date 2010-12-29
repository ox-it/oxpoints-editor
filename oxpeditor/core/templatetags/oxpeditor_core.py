from django import template

register = template.Library()

@register.filter(name='any')
def any_(value):
    return bool(value) and any(value)

@register.filter
def contains_comma(value):
    return ', ' in value

@register.filter(name='contains')
def contains_(value, arg):
    return arg in value
