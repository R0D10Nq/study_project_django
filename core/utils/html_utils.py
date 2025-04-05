"""
Утилиты для работы с HTML и шаблонами
"""
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup
from scour.scour import scourString

def prettify_html(string):
    """
    Форматирование HTML
    :param string: HTML-строка
    :return: str
    """
    if not string:
        return ""

    soup = BeautifulSoup(string, "html.parser")
    return soup.prettify()


def module(name, file, universal, variables=None):
    """
    Подключаем модуль
    :param name: Имя модуля
    :param file: Имя файла
    :param variables: Переменные
    :return: HTML
    """
    if not name:
        return ""

    # Получаем модуль
    module_name = get_module_name(name)
    
    # Определяем путь к шаблону
    if universal:
        template = f"modules_universal/{module_name}/template.html"
    else:
        template = f"modules/{module_name}/template.html"
    
    # Рендерим шаблон с переменными
    try:
        html = render_to_string(template, variables)
        return mark_safe(html)
    except Exception as e:
        return f"<!-- Ошибка подключения модуля {module_name}: {str(e)} -->"


def get_module_name(path: str):
    """
    Извлечь имя модуля
    :param path: Полное имя модуля
    :return: str
    """
    if not path:
        return ""

    # Удаляем префикс m-
    if path.startswith("m-"):
        return path
    
    # Удаляем путь, оставляем только имя файла
    path = path.split("/")[-1]
    path = path.split("\\")[-1]
    
    return path


# Импорт из других модулей (будет заменен на импорт из __init__.py)
from core.helpers import get_module_name
