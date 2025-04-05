"""
Утилиты для работы с внешними API (Albato, Telegram и т.д.)
"""
import json
import requests
import logging
from core.utils.landing_utils import get_landing

def send_to_albato(phone, name, quiz, wheel, url_page):
    """
    Отправка данных в Альбато
    :param phone: Телефон
    :param name: Имя
    :param quiz: Данные квиза
    :param wheel: Данные колеса
    :param url_page: URL страницы
    :return: dict
    """
    # Получаем лендинг
    landing = get_landing()
    if not landing:
        return {"success": False, "message": "Лендинг не найден"}
    
    # Получаем webhook
    webhook = get_albato_webhook(landing)
    if not webhook:
        return {"success": False, "message": "Webhook не найден"}
    
    # Формируем данные
    data = {
        "phone": phone,
        "name": name,
        "quiz": quiz,
        "wheel": wheel,
        "url_page": url_page
    }
    
    # Отправляем запрос
    try:
        response = requests.post(webhook, json=data)
        
        # Проверяем статус
        if response.status_code == 200:
            return {"success": True, "message": "Данные успешно отправлены"}
        else:
            return {"success": False, "message": f"Ошибка отправки: {response.status_code}"}
    
    except Exception as e:
        logging.error(f"Ошибка отправки в Albato: {str(e)}")
        return {"success": False, "message": f"Ошибка отправки: {str(e)}"}


def get_albato_webhook(landing=None):
    """
    Получить webhook для Albato
    :param landing: Инстанс лендинга
    :return: str
    """
    if not landing:
        landing = get_landing()
    
    if not landing:
        return None
    
    return landing.albato_webhook


def send_quiz_in_albato(landing=None):
    """
    Отправлять в альбато только квиз
    :param landing: Инстанс лендинга
    :return: bool
    """
    if not landing:
        landing = get_landing()
    
    if not landing:
        return False
    
    return landing.send_quiz_in_albato


def get_client_ip(request):
    """
    Получить IP клиента
    :param request: Запрос
    :return: str
    """
    if not request:
        return None
    
    # Проверяем заголовки
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    if x_forwarded_for:
        # Если есть X-Forwarded-For, берем первый IP
        ip = x_forwarded_for.split(',')[0]
    else:
        # Иначе берем REMOTE_ADDR
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


def get_client_phone(request):
    """
    Получить телефон клиента
    :param request: Запрос
    :return: str
    """
    if not request:
        return None
    
    # Проверяем куки
    phone = request.COOKIES.get('phone')
    
    # Если нет в куках, проверяем POST
    if not phone and request.method == 'POST':
        phone = request.POST.get('phone')
    
    # Если нет в POST, проверяем GET
    if not phone:
        phone = request.GET.get('phone')
    
    return phone


def get_fraud_list(base_name):
    """
    Получить базу, если нет или устарела
    :param base_name: Имя базы
    :return: list
    """
    # Здесь должна быть логика получения базы из внешнего источника
    # Для примера просто возвращаем пустой список
    return []


def user_is_fraud(request, check_type=None, param_value=None):
    """
    Пользователь бот?
    :param request: Запрос
    :param check_type: Тип проверки
    :param param_value: Значение параметра
    :return: bool
    """
    if not request:
        return False
    
    # Получаем IP
    ip = get_client_ip(request)
    
    # Проверяем IP в базе
    fraud_list = get_fraud_list('ip')
    
    if ip in fraud_list:
        return True
    
    # Если указан тип проверки
    if check_type and param_value:
        # Проверяем значение в базе
        fraud_list = get_fraud_list(check_type)
        
        if param_value in fraud_list:
            return True
    
    return False
