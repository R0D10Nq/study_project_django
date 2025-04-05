"""
Утилиты для кеширования
"""
from django.core.cache import cache
from functools import wraps
import inspect
import hashlib

def clear_landing_cache(landing=None, with_globals=False):
    """
    Удаление кэша представления
    :param landing: Инстанс лэндинга
    :param with_globals: Очистить глобальные переменные?
    """
    if not landing:
        from core.utils.landing_utils import get_landing
        landing = get_landing()
    
    if not landing:
        return
    
    # Очищаем кеш для конкретного лендинга
    cache_prefix = f"landing_{landing.id}_"
    keys = cache.keys(f"{cache_prefix}*")
    
    for key in keys:
        cache.delete(key)
    
    if with_globals:
        # Очищаем глобальные переменные
        cache.delete(f"globals_{landing.id}")


def cache_key(view=None, request=None):
    """
    Получить префикс кэша
    :param view: Представление
    :param request: Запрос
    :return: str
    """
    if not request:
        from django.middleware.csrf import get_token
        from crequest.middleware import CrequestMiddleware
        request = CrequestMiddleware.get_request()
    
    if not request:
        return None
    
    # Получаем имя представления
    if not view:
        view = view_name(request)
    
    # Получаем лендинг
    from core.utils.landing_utils import get_landing
    landing = get_landing()
    
    if not landing:
        return None
    
    # Формируем ключ кеша
    key = f"landing_{landing.id}_{view}"
    
    return key


def view_name(request=None):
    """
    Имя текущего view
    :param request: Запрос
    :return: str
    """
    if not request:
        from crequest.middleware import CrequestMiddleware
        request = CrequestMiddleware.get_request()
    
    if not request:
        return None
    
    # Получаем имя представления из resolver_match
    if hasattr(request, "resolver_match") and request.resolver_match:
        return request.resolver_match.view_name
    
    return None


def cache_page(*args, **kwargs):
    """
    Кеширование страницы
    :param args: Аргументы
    :param kwargs: Именованные аргументы
    :return: function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Получаем ключ кеша
            key = cache_key(view_func.__name__, request)
            
            if not key:
                return view_func(request, *args, **kwargs)
            
            # Проверяем наличие кеша
            cached_response = cache.get(key)
            
            if cached_response is not None:
                return cached_response
            
            # Получаем ответ
            response = view_func(request, *args, **kwargs)
            
            # Кешируем ответ
            cache.set(key, response, timeout=60 * 15)  # 15 минут
            
            return response
        
        return _wrapped_view
    
    # Если декоратор вызван без аргументов
    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    
    return decorator


def hash_string(string):
    """
    Хэширование строки
    :param string: Строка
    :return: str
    """
    if not string:
        return ""
    
    # Хешируем строку
    return hashlib.md5(string.encode()).hexdigest()
