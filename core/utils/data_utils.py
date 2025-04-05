"""
Утилиты для работы с данными (словари, списки, JSON и т.д.)
"""
import json
import re
from uuid import UUID

def jsonable(x):
    """
    Этот элемент сериализуется в JSON?
    :param x: Неизвестный элемент
    :return: bool
    """
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def empty_json():
    """
    Дефолтный, пустой JSON
    :return: dict
    """
    return {"success": True, "data": {}}


def unique_list(_list: list):
    """
    Уникализация списка
    :param _list: Список
    :return: list
    """
    if not _list:
        return []
    
    # Создаем новый список только с уникальными элементами
    unique = []
    for item in _list:
        if item not in unique:
            unique.append(item)
    
    return unique


def data_get(dictionary: dict, keys: str, default=None):
    """
    dot.notation доступ к атрибутам словаря
    :param dictionary: Словарь
    :param keys: Путь
    :param default: Значение по-умолчанию
    :return: mixed
    """
    if not dictionary or not keys:
        return default
    
    # Разбиваем путь на части
    keys = keys.split(".")
    
    # Проходим по пути
    result = dictionary
    for key in keys:
        # Если ключ - число, пробуем использовать его как индекс
        if key.isdigit() and isinstance(result, list):
            index = int(key)
            if 0 <= index < len(result):
                result = result[index]
            else:
                return default
        # Иначе используем как ключ словаря
        elif isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    
    return result


def recursive_find_by_key(obj, key):
    """
    Рекурсивный поиск значения по ключу в словаре
    :param obj: Словарь
    :param key: Ключ
    :return: mixed
    """
    if not obj or not key:
        return None
    
    # Если объект - словарь
    if isinstance(obj, dict):
        # Если ключ есть в словаре, возвращаем значение
        if key in obj:
            return obj[key]
        
        # Иначе ищем в значениях
        for k, v in obj.items():
            result = recursive_find_by_key(v, key)
            if result is not None:
                return result
    
    # Если объект - список
    elif isinstance(obj, list):
        # Ищем в элементах списка
        for item in obj:
            result = recursive_find_by_key(item, key)
            if result is not None:
                return result
    
    return None


def recursive_replace(data, needle, replace):
    """
    Рекурсивная замена
    :param data: Данные
    :param needle: Что заменить
    :param replace: На что заменить
    :return: mixed
    """
    if not data:
        return data
    
    # Если данные - строка
    if isinstance(data, str):
        return data.replace(needle, replace)
    
    # Если данные - словарь
    elif isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = recursive_replace(v, needle, replace)
        return result
    
    # Если данные - список
    elif isinstance(data, list):
        result = []
        for item in data:
            result.append(recursive_replace(item, needle, replace))
        return result
    
    return data


def is_valid_uuid(uuid_to_test, version=4):
    """
    Проверка UUID
    :param uuid_to_test: UUID для проверки
    :param version: Версия UUID
    :return: bool
    """
    if not uuid_to_test:
        return False
    
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
        return str(uuid_obj) == uuid_to_test
    except (ValueError, AttributeError, TypeError):
        return False


def wants_json(request):
    """
    Запрос требует ответа в формате JSON?
    :param request: Запрос
    :return: bool
    """
    if not request:
        return False
    
    # Проверяем заголовок Accept
    accept = request.META.get("HTTP_ACCEPT", "")
    
    # Проверяем параметр format
    format_param = request.GET.get("format", "")
    
    return "application/json" in accept or format_param == "json"
