"""
Утилиты для оптимизации статических ресурсов (JS, CSS).
Модуль содержит функции для объединения, минификации и кэширования ресурсов.
"""
import os
import re
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.cache import cache

class AssetOptimizer:
    """
    Класс для оптимизации статических ресурсов (JavaScript, CSS).
    Позволяет минимизировать количество запросов к серверу
    путем объединения и кэширования файлов.
    """
    # Кэш для хранения уже оптимизированных ресурсов
    _cache = {}
    
    # Шаблоны для замены URL в CSS
    CSS_URL_PATTERN = re.compile(r'url\(["\']?([^)"\']+)["\']?\)')
    
    @classmethod
    def combine_js_files(cls, module_name, file_paths, minify=True):
        """
        Объединяет несколько JS файлов в один и возвращает содержимое.
        
        :param module_name: Имя модуля, для которого объединяются файлы
        :param file_paths: Список относительных путей к JS файлам
        :param minify: Флаг, указывающий нужно ли минифицировать код
        :return: Строка с объединенным JS кодом
        """
        # Создаем уникальный ключ для кэша на основе путей и флага минификации
        cache_key = f"js_combined_{module_name}_{hashlib.md5(''.join(file_paths).encode()).hexdigest()}_{minify}"
        
        # Проверяем кэш
        cached_content = cache.get(cache_key)
        if cached_content:
            return cached_content
        
        combined_js = []
        
        # Обходим все файлы и объединяем их содержимое
        for file_path in file_paths:
            full_path = cls._resolve_path(file_path)
            if not full_path.exists():
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Если нужна минификация, удаляем комментарии и лишние пробелы
            if minify:
                content = cls._minify_js(content)
                
            # Добавляем разделитель между файлами
            combined_js.append(f"\n/* {os.path.basename(file_path)} */\n")
            combined_js.append(content)
        
        # Объединяем всё в одну строку
        result = "".join(combined_js)
        
        # Кэшируем результат
        cache.set(cache_key, result, 3600 * 24)  # Кэшируем на 24 часа
        
        return result
    
    @classmethod
    def combine_css_files(cls, module_name, file_paths, minify=True):
        """
        Объединяет несколько CSS файлов в один и возвращает содержимое.
        
        :param module_name: Имя модуля, для которого объединяются файлы
        :param file_paths: Список относительных путей к CSS файлам
        :param minify: Флаг, указывающий нужно ли минифицировать код
        :return: Строка с объединенным CSS кодом
        """
        # Создаем уникальный ключ для кэша
        cache_key = f"css_combined_{module_name}_{hashlib.md5(''.join(file_paths).encode()).hexdigest()}_{minify}"
        
        # Проверяем кэш
        cached_content = cache.get(cache_key)
        if cached_content:
            return cached_content
        
        combined_css = []
        
        # Обходим все файлы и объединяем их содержимое
        for file_path in file_paths:
            full_path = cls._resolve_path(file_path)
            if not full_path.exists():
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Исправляем относительные пути в url()
            base_dir = os.path.dirname(file_path)
            content = cls._fix_css_urls(content, base_dir)
            
            # Если нужна минификация, удаляем комментарии и лишние пробелы
            if minify:
                content = cls._minify_css(content)
                
            # Добавляем разделитель между файлами
            combined_css.append(f"\n/* {os.path.basename(file_path)} */\n")
            combined_css.append(content)
        
        # Объединяем всё в одну строку
        result = "".join(combined_css)
        
        # Кэшируем результат
        cache.set(cache_key, result, 3600 * 24)  # Кэшируем на 24 часа
        
        return result
    
    @staticmethod
    def _resolve_path(relative_path):
        """
        Преобразует относительный путь в абсолютный путь.
        
        :param relative_path: Относительный путь к файлу
        :return: Абсолютный путь к файлу (объект Path)
        """
        if os.path.isabs(relative_path):
            return Path(relative_path)
            
        # Если путь относительный, ищем файл в директориях проекта
        base_dirs = [
            settings.BASE_DIR / 'modules',
            settings.BASE_DIR / '_sites',
            settings.BASE_DIR / 'static',
        ]
        
        for base_dir in base_dirs:
            full_path = base_dir / relative_path
            if full_path.exists():
                return full_path
                
        # Если файл не найден, возвращаем исходный путь
        return Path(relative_path)
    
    @classmethod
    def _fix_css_urls(cls, css_content, base_dir):
        """
        Исправляет относительные URL в CSS на абсолютные.
        
        :param css_content: Содержимое CSS файла
        :param base_dir: Базовая директория CSS файла
        :return: CSS с исправленными URL
        """
        def replace_url(match):
            url = match.group(1)
            
            # Если URL начинается с / или содержит протокол (http:, https:, data:), оставляем как есть
            if url.startswith('/') or re.match(r'^(http|https|data):', url):
                return f"url('{url}')"
                
            # Иначе делаем URL относительно статического каталога
            static_url = settings.STATIC_URL.rstrip('/')
            return f"url('{static_url}/{base_dir}/{url}')"
            
        return cls.CSS_URL_PATTERN.sub(replace_url, css_content)
    
    @staticmethod
    def _minify_js(js_content):
        """
        Простая минификация JavaScript.
        Удаляет комментарии и лишние пробелы.
        
        :param js_content: Исходный JavaScript код
        :return: Минифицированный JavaScript
        """
        # Удаляем однострочные комментарии
        js_content = re.sub(r'//.*?$', '', js_content, flags=re.MULTILINE)
        
        # Удаляем многострочные комментарии
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Удаляем лишние пробелы в начале и конце строк
        js_content = re.sub(r'^\s+', '', js_content, flags=re.MULTILINE)
        js_content = re.sub(r'\s+$', '', js_content, flags=re.MULTILINE)
        
        # Удаляем повторяющиеся пробелы
        js_content = re.sub(r'\s{2,}', ' ', js_content)
        
        return js_content
    
    @staticmethod
    def _minify_css(css_content):
        """
        Простая минификация CSS.
        Удаляет комментарии и лишние пробелы.
        
        :param css_content: Исходный CSS код
        :return: Минифицированный CSS
        """
        # Удаляем комментарии
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Удаляем пробелы вокруг скобок, запятых, двоеточий и точек с запятой
        css_content = re.sub(r'\s*([{};:,])\s*', r'\1', css_content)
        
        # Удаляем пробелы в начале и конце строк
        css_content = re.sub(r'^\s+', '', css_content, flags=re.MULTILINE)
        css_content = re.sub(r'\s+$', '', css_content, flags=re.MULTILINE)
        
        # Удаляем повторяющиеся пробелы
        css_content = re.sub(r'\s{2,}', ' ', css_content)
        
        return css_content
