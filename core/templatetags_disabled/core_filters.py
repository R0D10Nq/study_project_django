from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def phone_format(value):
    """
    Форматирует номер телефона в читаемый вид
    
    Пример:
    {{ "+79991234567"|phone_format }} -> +7 (999) 123-45-67
    """
    if not value:
        return ''
    
    # Удаляем все нецифры и + из номера
    digits = re.sub(r'[^\d+]', '', str(value))
    
    # Если номер начинается с 8, заменяем на +7
    if digits.startswith('8') and len(digits) == 11:
        digits = '+7' + digits[1:]
    
    # Если номер начинается с 7, добавляем +
    if digits.startswith('7') and len(digits) == 11:
        digits = '+' + digits
    
    # Форматируем номер
    if digits.startswith('+7') and len(digits) == 12:
        return f'{digits[:2]} ({digits[2:5]}) {digits[5:8]}-{digits[8:10]}-{digits[10:12]}'
    
    # Если формат не распознан, возвращаем как есть
    return value


@register.filter
def price_format(value):
    """
    Форматирует цену в читаемый вид с пробелами между разрядами
    
    Пример:
    {{ 1234567|price_format }} -> 1 234 567
    """
    if not value:
        return '0'
    
    try:
        # Преобразуем в число и форматируем
        num = int(float(str(value).replace(' ', '')))
        return '{:,}'.format(num).replace(',', ' ')
    except (ValueError, TypeError):
        return value


@register.filter
def strip_tags(value):
    """
    Удаляет HTML-теги из строки
    
    Пример:
    {{ "<p>Текст</p>"|strip_tags }} -> Текст
    """
    if not value:
        return ''
    
    # Простая реализация удаления тегов
    return re.sub(r'<[^>]*>', '', str(value))


@register.filter
def truncate_chars(value, max_length):
    """
    Обрезает текст до указанной длины и добавляет многоточие
    
    Пример:
    {{ "Длинный текст"|truncate_chars:10 }} -> Длинный...
    """
    if not value:
        return ''
    
    value = str(value)
    
    if len(value) <= max_length:
        return value
    
    return value[:max_length] + '...'
