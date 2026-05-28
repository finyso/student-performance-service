from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получение элемента из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)