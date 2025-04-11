"""
Теги шаблонов для оптимизации и управления статическими ресурсами.
Позволяют объединять и минифицировать JS и CSS файлы на лету.
"""
import os
from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.conf import settings
from core.utils.assets import AssetOptimizer

register = template.Library()


@register.simple_tag(takes_context=True)
def combine_js(context, module, *args, minify=True):
    """
    Тег для объединения нескольких JavaScript файлов из модуля в один.
    
    Пример использования:
    {% combine_js 'm-header' 'script.js' 'additional.js' %}
    
    :param context: Контекст шаблона
    :param module: Имя модуля
    :param args: Пути к JavaScript файлам
    :param minify: Флаг, указывающий нужно ли минифицировать код
    :return: HTML-тег script с объединенным JavaScript
    """
    if not args:
        return ''
        
    # Получаем текущий лендинг из контекста
    landing = context.get('landing')
    if not landing:
        return ''
    
    # Строим полные пути к файлам с учетом модульной структуры
    file_paths = []
    for filename in args:
        # Основной путь к файлу в текущем модуле для текущего лендинга
        path = f"{module}/{landing.app_name}/{filename}"
        file_paths.append(path)
        
        # Если файл не существует в директории лендинга, используем общий файл
        if not os.path.exists(os.path.join(settings.BASE_DIR, 'modules', path)):
            path = f"{module}/{filename}"
            file_paths[-1] = path
    
    # Объединяем файлы
    combined_js = AssetOptimizer.combine_js_files(module, file_paths, minify=minify)
    
    # Формируем HTML-тег
    return mark_safe(f'<script>{combined_js}</script>')


@register.simple_tag(takes_context=True)
def combine_css(context, module, *args, minify=True):
    """
    Тег для объединения нескольких CSS файлов из модуля в один.
    
    Пример использования:
    {% combine_css 'm-header' 'style.css' 'responsive.css' %}
    
    :param context: Контекст шаблона
    :param module: Имя модуля
    :param args: Пути к CSS файлам
    :param minify: Флаг, указывающий нужно ли минифицировать код
    :return: HTML-тег style с объединенным CSS
    """
    if not args:
        return ''
        
    # Получаем текущий лендинг из контекста
    landing = context.get('landing')
    if not landing:
        return ''
    
    # Строим полные пути к файлам с учетом модульной структуры
    file_paths = []
    for filename in args:
        # Основной путь к файлу в текущем модуле для текущего лендинга
        path = f"{module}/{landing.app_name}/{filename}"
        file_paths.append(path)
        
        # Если файл не существует в директории лендинга, используем общий файл
        if not os.path.exists(os.path.join(settings.BASE_DIR, 'modules', path)):
            path = f"{module}/{filename}"
            file_paths[-1] = path
    
    # Объединяем файлы
    combined_css = AssetOptimizer.combine_css_files(module, file_paths, minify=minify)
    
    # Формируем HTML-тег
    return mark_safe(f'<style>{combined_css}</style>')


@register.simple_tag
def versioned_static(path):
    """
    Версионирует статические файлы для инвалидации кэша браузера при изменениях.
    Добавляет к URL параметр v с хешем файла.
    
    Пример использования:
    <img src="{% versioned_static 'images/logo.png' %}">
    
    :param path: Путь к статическому файлу
    :return: URL к статическому файлу с добавленным параметром версии
    """
    static_url = static(path)
    
    # Проверяем, существует ли файл
    file_path = os.path.join(settings.STATIC_ROOT, path)
    if not os.path.exists(file_path):
        return static_url
    
    # Получаем время последнего изменения файла и используем его как версию
    mtime = int(os.path.getmtime(file_path))
    return f"{static_url}?v={mtime}"


@register.simple_tag(takes_context=True)
def module_js(context, module_name):
    """
    Автоматически собирает и подключает все JS файлы из указанного модуля.
    
    Пример использования:
    {% module_js 'm-header' %}
    
    :param context: Контекст шаблона
    :param module_name: Имя модуля
    :return: HTML-тег script с JavaScript кодом модуля
    """
    landing = context.get('landing')
    if not landing:
        return ''
    
    # Ищем все JS файлы в директории модуля
    module_dir = os.path.join(settings.BASE_DIR, 'modules', module_name, landing.app_name)
    if not os.path.exists(module_dir):
        module_dir = os.path.join(settings.BASE_DIR, 'modules', module_name)
        if not os.path.exists(module_dir):
            return ''
    
    # Получаем список файлов .js
    js_files = [f for f in os.listdir(module_dir) if f.endswith('.js')]
    if not js_files:
        return ''
    
    # Используем combine_js для объединения найденных файлов
    return combine_js(context, module_name, *js_files)


@register.simple_tag(takes_context=True)
def module_css(context, module_name):
    """
    Автоматически собирает и подключает все CSS файлы из указанного модуля.
    
    Пример использования:
    {% module_css 'm-header' %}
    
    :param context: Контекст шаблона
    :param module_name: Имя модуля
    :return: HTML-тег style с CSS кодом модуля
    """
    landing = context.get('landing')
    if not landing:
        return ''
    
    # Ищем все CSS файлы в директории модуля
    module_dir = os.path.join(settings.BASE_DIR, 'modules', module_name, landing.app_name)
    if not os.path.exists(module_dir):
        module_dir = os.path.join(settings.BASE_DIR, 'modules', module_name)
        if not os.path.exists(module_dir):
            return ''
    
    # Получаем список файлов .css
    css_files = [f for f in os.listdir(module_dir) if f.endswith('.css')]
    if not css_files:
        return ''
    
    # Используем combine_css для объединения найденных файлов
    return combine_css(context, module_name, *css_files)
