"""
Модуль с middleware для оптимизации фронтенда и управления кэшированием.
"""
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import re

class StaticFilesOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware для оптимизации статических файлов и правильного кэширования.
    Добавляет заголовки кэширования для статических файлов и сжимает контент,
    если клиент поддерживает сжатие.
    """
    CACHEABLE_CONTENT_TYPES = {
        'text/css',
        'application/javascript',
        'application/x-javascript',
        'text/javascript',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/gif',
        'image/webp',
        'image/svg+xml',
        'font/woff',
        'font/woff2',
        'application/font-woff',
        'application/font-woff2',
    }
    
    # Файлы, которые никогда не кэшируются
    NEVER_CACHE_PATHS = [
        '/admin/',
        '/api/',
    ]
    
    # Регулярное выражение для идентификации статических файлов
    STATIC_FILE_REGEX = re.compile(
        r'\.(css|js|png|jpg|jpeg|gif|webp|svg|woff|woff2|ttf|eot|ico)$'
    )
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.is_debug = settings.DEBUG
        # В debug режиме кэшируем меньше времени
        self.cache_timeout = 60 if self.is_debug else 31536000  # 1 минута в debug, 1 год в production
    
    def process_response(self, request, response):
        """
        Обработка ответа: добавление заголовков кэширования,
        сжатие контента и другие оптимизации.
        """
        path = request.path_info.lower()
        
        # Никогда не кэшируем некоторые пути
        for never_cache_path in self.NEVER_CACHE_PATHS:
            if path.startswith(never_cache_path):
                add_never_cache_headers(response)
                return response
        
        # Проверяем, является ли запрашиваемый файл статическим
        is_static_file = bool(self.STATIC_FILE_REGEX.search(path))
        content_type = response.get('Content-Type', '').split(';')[0]
        
        # Если это статический файл или контент, который можно кэшировать
        if is_static_file or content_type in self.CACHEABLE_CONTENT_TYPES:
            # Устанавливаем заголовки для кэширования
            response['Cache-Control'] = f'public, max-age={self.cache_timeout}'
            response['Expires'] = None  # Удаляем заголовок Expires, если он есть
            
            # Для JavaScript и CSS файлов добавляем хеш-суммы для версионирования
            if content_type in ('text/css', 'application/javascript', 'text/javascript'):
                response['ETag'] = f'"{hash(response.content)}"'
        
        # Возвращаем модифицированный ответ
        return response


class XSSProtectionMiddleware(MiddlewareMixin):
    """
    Middleware для защиты от XSS-атак.
    Добавляет соответствующие заголовки безопасности ко всем ответам.
    """
    def process_response(self, request, response):
        """
        Добавляет заголовки безопасности для защиты от XSS-атак.
        """
        # Добавляем заголовок X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Добавляем Content-Security-Policy для блокировки небезопасных ресурсов
        # Этот заголовок ограничивает загрузку ресурсов с других доменов
        if not settings.DEBUG:
            # В production используем более строгие правила
            csp_value = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
            response['Content-Security-Policy'] = csp_value
        
        # Запрещаем браузеру угадывать тип контента, что может привести к XSS
        response['X-Content-Type-Options'] = 'nosniff'
        
        return response
