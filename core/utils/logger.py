"""
Модуль для логирования.
Предоставляет набор функций для логирования событий в системе с разными уровнями важности.
"""
import logging
import traceback
import inspect
from functools import wraps
from datetime import datetime

# Настройка стандартного логгера
logger = logging.getLogger('django')

# Специализированные логгеры
chunks_logger = logging.getLogger('chunks')
security_logger = logging.getLogger('security')
performance_logger = logging.getLogger('performance')


class LogLevels:
    """
    Константы для уровней логирования.
    """
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class Log:
    """
    Класс для логирования событий в системе.
    Предоставляет статические методы для логирования событий разных типов.
    """
    
    @staticmethod
    def info(message, module=None):
        """
        Логирует информационное сообщение.
        
        :param message: Сообщение для логирования
        :param module: Имя модуля (опционально)
        """
        module_name = module or inspect.currentframe().f_back.f_globals.get('__name__', 'unknown')
        logger.info(f"[{module_name}] {message}")
    
    @staticmethod
    def warning(message, module=None):
        """
        Логирует предупреждение.
        
        :param message: Предупреждающее сообщение
        :param module: Имя модуля (опционально)
        """
        module_name = module or inspect.currentframe().f_back.f_globals.get('__name__', 'unknown')
        logger.warning(f"[{module_name}] {message}")
    
    @staticmethod
    def error(message, module=None, exception=None):
        """
        Логирует ошибку.
        
        :param message: Сообщение об ошибке
        :param module: Имя модуля (опционально)
        :param exception: Объект исключения (опционально)
        """
        module_name = module or inspect.currentframe().f_back.f_globals.get('__name__', 'unknown')
        if exception:
            tb = traceback.format_exc()
            logger.error(f"[{module_name}] {message}: {str(exception)}\n{tb}")
        else:
            logger.error(f"[{module_name}] {message}")
    
    @staticmethod
    def critical(message, module=None, exception=None):
        """
        Логирует критическую ошибку.
        
        :param message: Сообщение о критической ошибке
        :param module: Имя модуля (опционально)
        :param exception: Объект исключения (опционально)
        """
        module_name = module or inspect.currentframe().f_back.f_globals.get('__name__', 'unknown')
        if exception:
            tb = traceback.format_exc()
            logger.critical(f"[{module_name}] {message}: {str(exception)}\n{tb}")
        else:
            logger.critical(f"[{module_name}] {message}")
    
    @staticmethod
    def debug(message, module=None):
        """
        Логирует отладочное сообщение.
        
        :param message: Отладочное сообщение
        :param module: Имя модуля (опционально)
        """
        module_name = module or inspect.currentframe().f_back.f_globals.get('__name__', 'unknown')
        logger.debug(f"[{module_name}] {message}")
    
    @staticmethod
    def performance(message, time_taken=None):
        """
        Логирует информацию о производительности.
        
        :param message: Сообщение
        :param time_taken: Время выполнения в секундах (опционально)
        """
        log_msg = message
        if time_taken is not None:
            log_msg = f"{message} (Выполнено за {time_taken:.3f} сек)"
        performance_logger.info(log_msg)
    
    @staticmethod
    def security(message, level='info', request=None):
        """
        Логирует информацию, связанную с безопасностью.
        
        :param message: Сообщение
        :param level: Уровень логирования (info, warning, error, critical)
        :param request: Объект запроса (опционально)
        """
        ip = None
        user = None
        
        if request:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        
        log_msg = f"{message}"
        if ip and user:
            log_msg = f"{message} [IP: {ip}, User: {user}]"
        
        if level == 'warning':
            security_logger.warning(log_msg)
        elif level == 'error':
            security_logger.error(log_msg)
        elif level == 'critical':
            security_logger.critical(log_msg)
        else:
            security_logger.info(log_msg)


def log_exception(e, module=None):
    """
    Логирует исключение с полным стектрейсом.
    
    :param e: Исключение
    :param module: Имя модуля, в котором произошло исключение (опционально)
    """
    tb = traceback.format_exc()
    module_name = module or inspect.currentframe().f_back.f_globals.get('__name__', 'unknown')
    logger.error(f"Exception in {module_name}: {str(e)}\n{tb}")
    

def log_performance(message, time_taken=None):
    """
    Логирует информацию о производительности операции.
    
    :param message: Сообщение
    :param time_taken: Время выполнения операции в секундах (опционально)
    """
    log_msg = message
    if time_taken is not None:
        log_msg = f"{message} (Выполнено за {time_taken:.3f} сек)"
    performance_logger.info(log_msg)


def log_security(message, level='info', request=None):
    """
    Логирует информацию, связанную с безопасностью.
    
    :param message: Сообщение
    :param level: Уровень логирования (info, warning, error, critical)
    :param request: Объект запроса (опционально)
    """
    ip = None
    user = None
    
    if request:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
    
    log_msg = f"{message}"
    if ip and user:
        log_msg = f"{message} [IP: {ip}, User: {user}]"
    
    if level == 'warning':
        security_logger.warning(log_msg)
    elif level == 'error':
        security_logger.error(log_msg)
    elif level == 'critical':
        security_logger.critical(log_msg)
    else:
        security_logger.info(log_msg)


def log_chunk_operation(operation, chunk_name, success=True, error=None):
    """
    Логирует операции с чанками.
    
    :param operation: Тип операции (create, update, delete, render)
    :param chunk_name: Имя чанка
    :param success: Флаг успешности операции
    :param error: Текст ошибки, если операция не удалась
    """
    if success:
        chunks_logger.info(f"Chunk {operation}: {chunk_name} - SUCCESS")
    else:
        chunks_logger.error(f"Chunk {operation}: {chunk_name} - FAILED: {error}")


def timing_decorator(func):
    """
    Декоратор для измерения времени выполнения функции.
    
    :param func: Декорируемая функция
    :return: Обернутая функция с логированием времени выполнения
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        
        time_taken = (end_time - start_time).total_seconds()
        log_performance(f"Function {func.__name__} executed", time_taken)
        
        return result
    return wrapper
