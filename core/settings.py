"""
Настройки ядра проекта.
Этот файл содержит базовые настройки для core модуля.
"""
import os
import sys
from pathlib import Path

# Предотвращаем циклический импорт
try:
    from django.conf import settings
    # Получаем BASE_DIR из главных настроек проекта
    BASE_DIR = settings.BASE_DIR
except (ImportError, AttributeError):
    # Если не получается импортировать из Django settings, используем резервный вариант
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent

# Директории для статических файлов модулей
MODULES_DIR = os.path.join(BASE_DIR, 'modules')

# Директории для сайтов
SITES_DIR = os.path.join(BASE_DIR, '_sites')

# Настройки окружения
try:
    ENVIRONMENT = settings.ENVIRONMENT
except (NameError, AttributeError):
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Константы для типов чанков
CHUNK_TYPE_TEXT = 'text'
CHUNK_TYPE_HTML = 'html'
CHUNK_TYPE_JSON = 'json'
CHUNK_TYPE_CSS = 'css'
CHUNK_TYPE_JS = 'js'

# Константы для статусов лендингов
LANDING_STATUS_ACTIVE = 'active'
LANDING_STATUS_INACTIVE = 'inactive'
LANDING_STATUS_DELETED = 'deleted'
LANDING_STATUS_DEVELOPMENT = 'development'
LANDING_STATUS_MODERATION = 'moderation'

# Настройки кэширования
CACHE_TIMEOUT = 3600  # 1 час по умолчанию
CACHE_CHUNK_TIMEOUT = 86400  # 24 часа для чанков
CACHE_TEMPLATE_TIMEOUT = 3600 * 12  # 12 часов для шаблонов

# Медиа файлы
try:
    MEDIA_URL = settings.MEDIA_URL
except (NameError, AttributeError):
    MEDIA_URL = '/media/'