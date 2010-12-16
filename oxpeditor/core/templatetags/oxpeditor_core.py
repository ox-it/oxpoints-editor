from django import template

register = template.Library()

@register.filter(name='any')
def any_(value):
    return bool(value) and any(value)
