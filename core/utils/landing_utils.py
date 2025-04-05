"""
Утилиты для работы с лендингами
"""
from django.core.cache import cache
from crequest.middleware import CrequestMiddleware
from core.models import Landing, Page

def make_host_key(host):
    """Очищает ключ лэндинга"""
    host = host.replace("-", "_")
    return host.replace(".", "__")


def get_template(app_name):
    """Получить шаблон для приложения"""
    if app_name:
        app_settings = importlib.import_module(f"_sites.{app_name}.settings")
        if app_settings:
            return app_settings.TEMPLATE_SITE
        else:
            return None


def get_current_host(landing=None, raw=False):
    """Достать текущий хост"""
    if type(landing) is Landing:
        host = landing.domain
        host = re.match(r"^(.+?)(:|$)", host).group(1)
    else:
        request = CrequestMiddleware.get_request()

        if not request:
            return None

        host = request.get_host()
        host = re.match(r"^(.+?)(:|$)", host).group(1)

    if raw:
        return host

    return make_host_key(host)


def get_landing():
    """Достать текущий лэндинг"""
    request = CrequestMiddleware.get_request()
    if not request:
        return None
    return getattr(request, "landing", None)


def get_current_page():
    """Достать текущую страницу"""
    request = CrequestMiddleware.get_request()
    if not request:
        return None
    return getattr(request, "page", None)


def get_emails(landing=None):
    """Достать Email'ы для заявок лэндинга"""
    if not landing:
        landing = get_landing()
    if not landing:
        return None
    return landing.emails


# Импортируем необходимые модули
import re
import importlib
