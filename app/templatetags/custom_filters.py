from django import template

register = template.Library()

@register.filter
def index(lst, i):
    try:
        return lst[i]
    except:
        return ''

@register.filter
def zip_lists(list1, list2):
    return list(zip(list1, list2))

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
@register.filter
def sub(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return 0

@register.filter
def abs(value):
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value 