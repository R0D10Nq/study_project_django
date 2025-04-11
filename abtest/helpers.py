"""
Заглушка для модуля abtest.helpers, необходимого для работы проекта.
Здесь реализованы базовые функции, которые могут вызываться из других модулей.
"""
import logging

logger = logging.getLogger('chunks')

def get_version():
    """
    Возвращает текущую версию A/B тестирования.
    Заглушка для функции, которая определяет, какую версию (A или B) контента
    следует отображать пользователю.
    
    :return: str - 'a' или 'b' в качестве версии
    """
    logger.info("A/B testing: Returning default version 'a'")
    return 'a'
    
def get_version_by_request(request):
    """
    Определяет версию A/B тестирования на основе запроса пользователя.
    
    :param request: HttpRequest - объект запроса Django
    :return: str - 'a' или 'b' в качестве версии
    """
    # В заглушке всегда возвращаем версию 'a'
    return get_version()

def set_ab_cookie(response, version):
    """
    Устанавливает cookie для определения версии A/B теста.
    
    :param response: HttpResponse - объект ответа Django
    :param version: str - версия ('a' или 'b')
    :return: HttpResponse - объект ответа с установленной cookie
    """
    # Устанавливаем cookie с версией на 30 дней
    response.set_cookie('ab_version', version, max_age=60*60*24*30)
    return response
