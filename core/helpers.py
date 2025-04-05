import inspect
from pathlib import Path
from pyclbr import Class
from types import ModuleType
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.db.models import Q
from functools import reduce
from crequest.middleware import CrequestMiddleware
from abtest.helpers import get_version
from core.chunks.helpers import get_chunks
from core.data import GLOBAL_VARS
from core.models import Landing, Page, EList
from core.settings import BASE_DIR, ENVIRONMENT, MEDIA_URL
from core.utils.elist import EditableList
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageSequence
from uuid import UUID
import json, re, os, dotenv, logging, importlib, math, requests, datetime, time, subprocess, stat, pillow_heif, sass

from core.utils.logger import Log, LogLevels

from scour.scour import scourString


def make_host_key(host):
    """Очищает ключ лэндинга"""
    host = host.replace("-", "_")

    return host.replace(".", "__")


def get_template(app_name):
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

        host = re.match(r"^(.+?)(:|$)", request.get_host()).group(1)

    cached_host = GLOBAL_VARS.get("landings").get(host)

    if cached_host:
        return cached_host

    if not cached_host:
        landing = Landing.objects.filter(Q(domain=host) | Q(local_domain=host) | Q(dev_domain=host)).first()
        if landing:
            GLOBAL_VARS["landings"][host] = make_host_key(landing.domain)

    return host if raw else GLOBAL_VARS.get("landings").get(host)


def pp(object):
    """PrettyPrint obj"""
    import pprint

    pp_instance = pprint.PrettyPrinter(indent=4)
    pp_instance.pprint(object)


def prettify_html(string) -> str:
    """Форматирование HTML
    :param string: HTML-строка
    :return: str
    """
    if not string:
        return string

    if isinstance(string, int) or isinstance(string, float):
        return str(string)

    if string.endswith((".jpg", ".jpeg", ".png", ".svg", ".webp")) or string.startswith("http"):
        return string

    r = re.compile(r"^(\s*)", re.MULTILINE)

    string = r.sub(r"\1" * 4, BeautifulSoup(str(string), features="html.parser").prettify())

    return mark_safe(string.strip()) if string else ""


def get_landing() -> Landing:
    """Достать текущий лэндинг
    :return: Landing
    """
    return GLOBAL_VARS.get(get_current_host(), {}).get("landing")


def get_current_page() -> Landing:
    """Достать текущую страницу
    :return: Landing
    """
    return GLOBAL_VARS.get(get_current_host(), {}).get("page")


def get_emails(landing=None):
    """Достать Email'ы для заявок лэндинга"""
    landing = landing if landing else get_landing()

    if not landing or not landing.emails:
        return set()

    emails = landing.emails.splitlines()

    return set(map(lambda email: email.strip(), emails))


def get_tg_token(landing=None):
    """Получить tg-токен бота для заявок лэндинга"""
    landing = landing if landing else get_landing()

    return landing.tg_token if landing else None


def get_tg_chat_id(landing=None):
    """Получить id чата, куда отправится сообщение"""
    landing = landing if landing else get_landing()

    return landing.tg_chat_id if landing else None


def get_albato_webhook(landing=None):
    """Получить webhook для Albato"""
    landing = landing if landing else get_landing()

    return landing.albato_webhook if landing else None


def send_quiz_in_albato(landing=None):
    """Отправлять в альбато только квиз"""

    landing = landing if landing else get_landing()
    return landing.send_quiz_in_albato if landing else False


def get_amocrm_deal_tag(landing=None):
    """Получить тэг для сделок AmoCRM"""
    landing = landing if landing else get_landing()

    return landing.amocrm_deal_tag if landing else None


def get_yandex_metrika_id(landing=None):
    """Получить ID Яндекс.Метрики для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.yandex_metrika_id if landing else None


def get_utm_campaign(landing=None):
    """Получить название рекламной компании"""
    landing = landing if landing else get_landing()

    return landing.utm_campaign if landing else None


def get_google_analytics_id(landing=None):
    """Получить ID Google Аналитики для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.google_analytics_id if landing else None


def get_vk_pixel_id(landing=None):
    """Получить ID Пикселя ВК для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.vk_pixel_id if landing else None


def get_top_mail_id(landing=None):
    """Получить ID Пикселя Нового Кабинета ВК для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.top_mail_id if landing else None


def get_roistat_id(landing=None):
    """Получить ID Roistat для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.roistat_id if landing else None


def get_mailer_login(landing=None):
    """Получить smtp_login лендинга"""
    landing = landing if landing else get_landing()

    return landing.mailer_smtp_login if landing else None


def get_mailer_host(landing=None):
    """Получить smtp_login лендинга"""
    landing = landing if landing else get_landing()

    return landing.mailer_smtp_host if landing else None


def get_mailer_password(landing=None):
    """Получить smtp_password лендинга"""
    landing = landing if landing else get_landing()

    return landing.mailer_smtp_password if landing else None


def get_mailer_from(landing=None):
    """Получить mail_from лендинга"""
    landing = landing if landing else get_landing()

    return landing.mailer_mail_from if landing else None


def get_mailer_subject(landing=None):
    """Получить mail_subject лендинга"""
    landing = landing if landing else get_landing()

    return landing.mailer_mail_subject if landing else None


def ignore_direct_entry(landing=None):
    """Не принимать заявки без источника?"""
    landing = landing if landing else get_landing()

    return landing.ignore_direct_entry if landing else False


def get_blacklist_utm(landing=None):
    """Достать чёрный список utm-меток"""

    landing = landing if landing else get_landing()

    if not landing or not landing.blacklist_utm:
        return list()

    return landing.blacklist_utm.splitlines()


def scan_blacklist_utm(request, is_json=True):
    from django.http import JsonResponse

    # Делает теневую отправку если РК есть в списке

    utm_blacklist = get_blacklist_utm()
    utm_in_blacklist = False
    utm_search_list = ["utm_campaign", "utm_content", "utm_medium", "calltouch_tm", "utm_source", "cm_id", "utm_term"]

    if utm_blacklist:
        keys_to_delete = []
        for key, value in request.session.items():
            if key in utm_search_list:
                keys_to_delete.append(key)
                for needle in utm_blacklist:
                    if str(needle).lower().strip() in str(value).lower().strip():
                        utm_in_blacklist = True
                        break

        for key in keys_to_delete:
            del request.session[key]

    return JsonResponse({"success": utm_in_blacklist}) if is_json else utm_in_blacklist


def get_roistat_and_ct(landing=None):
    """Подключить скрипт Roistat+Calltouch для лэндинга?"""
    landing = landing if landing else get_landing()

    return landing.roistat_and_ct if landing else None


def get_toolbox_account_id(landing=None):
    """Получить ID аккаунта в тулбоксе для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.toolbox_account_id if landing else None


def get_calltouch(landing=None):
    """Получить настройки КТ для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.calltouch if landing else None


def get_custom_meta_tags(landing=None):
    """Получить кастомные мета-теги для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.custom_meta_tags if landing else None


def hide_copyright(landing=None):
    """Скрыть копирайты Синергиум?"""
    landing = landing if landing else get_landing()

    return landing.hide_copyright if landing else False


def hide_modal_dont_go(landing=None):
    """Не показывать модальное окно dont-go?"""
    landing = landing if landing else get_landing()

    return landing.hide_modal_dont_go if landing else False


def show_cookies(landing=None):
    """Включить cookies?"""
    landing = landing if landing else get_landing()

    return landing.show_cookies if landing else False


def show_snow(landing=None):
    """Включить снег?"""
    landing = landing if landing else get_landing()

    return landing.show_snow if landing else False


def show_scroll(landing=None):
    """Отображать скролл наверх?"""
    landing = landing if landing else get_landing()

    return landing.show_scroll if landing else False


def on_moderation(landing=None):
    """Лэндинг на модерации?"""
    landing = landing if landing else get_landing()

    return landing.moderation if landing else False


def is_ab_test(landing=None):
    """Включено ли A/B тестирование?"""
    landing = landing if landing else get_landing()

    return landing.ab_test if landing else False


def is_new_year():
    """Новый год?"""
    date = datetime.date.today()
    month = date.month
    day = date.day
    landing = get_landing()
    offer_date = "18/9"

    if not landing:
        return False

    elist = EList.objects.filter(landing_id=landing.id, name="settings_new_year")
    for elem in elist.values("list"):
        if elem["list"]["1"]["offer_date"]:
            offer_date = elem["list"]["1"]["offer_date"]
    offer_date = offer_date.split("/")
    day_start, day_end = int(offer_date[0]), int(offer_date[1])

    return (day >= day_start and month == 12) or (day <= day_end and month == 1)


def is_holidays():
    """Майские праздники?"""
    date = datetime.date
    today = date.today()

    return (today.month == 4 and today.day >= 26) or (today.month == 5 and today.day < 14)


def is_b_version(landing=None):
    """Включена версия B?"""
    landing = landing if landing else get_landing()

    return landing.b_version if landing else False


def get_activity_goals(landing=None):
    """Получить цели активности для лэндинга"""
    landing = landing if landing else get_landing()

    return landing.activity_goals if landing else None


def on_antispam(landing=None):
    """На лендинге включена защита от спама?"""
    landing = landing if landing else get_landing()

    return landing.antispam if landing else False


def get_page() -> Page:
    """Достать текущую страницу
    :return: Page
    """
    return GLOBAL_VARS.get(get_current_host(), {}).get("page")


def get_request():
    """Достать текущий запрос"""
    return GLOBAL_VARS.get(get_current_host(), {}).get("request")


def get_elist(landing=None):
    """Достать все elist для текущего лэндинга"""
    landing = landing if landing else get_landing()
    host_key = get_current_host(landing)

    return GLOBAL_VARS.get(host_key, {}).get(f"elist_{landing.app_name}", {})


def settings(landing=None) -> ModuleType:
    """Настройки"""
    landing = landing if landing else get_landing()
    host_key = get_current_host(landing)

    if type(landing) is Landing:
        if not GLOBAL_VARS.get(host_key):
            GLOBAL_VARS[host_key] = {}

        if not GLOBAL_VARS.get(host_key) and not CrequestMiddleware.get_request():
            return importlib.import_module(f"_sites.{landing.app_name}.settings")

        if not GLOBAL_VARS.get(host_key, {}).get(f"landing_settings_{landing.app_name}"):
            GLOBAL_VARS[host_key][f"landing_settings_{landing.app_name}"] = importlib.import_module(f"_sites.{landing.app_name}.settings")

        return GLOBAL_VARS.get(host_key).get(f"landing_settings_{landing.app_name}")
    else:
        if not GLOBAL_VARS.get("core_settings"):
            GLOBAL_VARS["core_settings"] = importlib.import_module("core.settings")

        return GLOBAL_VARS.get("core_settings")


def env(env_key: str, landing=None):
    """Получить переменную среды
    :param env_key: Имя переменной среды
    :param landing: Инстанс лэндинга
    """
    landing = landing if landing else get_landing()

    if type(landing) is Landing:
        dotenv.read_dotenv(settings(landing).BASE_DIR / f"_sites/{landing.app_name}/.env", override=True)

    return os.environ.get(env_key, None)


def get_landing_data(landing=None):
    """Получить данные для лэндинга"""
    landing = landing if landing else get_landing()
    host_key = get_current_host(landing)

    if type(landing) is Landing:
        if not GLOBAL_VARS.get(host_key, {}).get(f"data_{landing.app_name}"):
            GLOBAL_VARS[host_key][f"data_{landing.app_name}"] = importlib.import_module(f"_sites.{landing.app_name}.data._common").DATA

            app_data_files = os.listdir(settings().BASE_DIR / f"_sites/{landing.app_name}/data")
            app_data_import_path = f"_sites.{landing.app_name}.data"
            universal_data_files = os.listdir(settings().BASE_DIR / "modules_universal/data_universal")
            universal_data_import_path = "modules_universal.data_universal"

            data_files_settings = {
                app_data_import_path: app_data_files,
                universal_data_import_path: universal_data_files,
            }

            for data_module_path, data_files in data_files_settings.items():
                for file in data_files:

                    if file == "_common.py" or not file.endswith(".py"):
                        continue

                    file = os.path.splitext(file)[0]

                    GLOBAL_VARS[host_key][f"data_{landing.app_name}"] = GLOBAL_VARS[host_key][f"data_{landing.app_name}"] | {
                        f"{file}": importlib.import_module(f"{data_module_path}.{file}").DATA
                    }

    return GLOBAL_VARS.get(host_key).get(f"data_{landing.app_name}") if landing else {}


def jsonable(x) -> bool:
    """Этот элемент сериализуется в JSON?
    :param x: Неизвестный элемент
    :return: bool
    """
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def wants_json(request) -> bool:
    """Запрос требует ответа в формате JSON?
    :param request: Запрос
    :return: bool
    """
    accept = request.META.get("HTTP_ACCEPT")
    return ("/json" in accept) or ("+json" in accept)


def log_queries_to_console():
    """Логирование всех запросов в консоль"""
    logger = logging.getLogger("django.db.backends")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())


def empty_json() -> dict:
    """Дефолтный, пустой JSON"""
    return {}


def unique_list(_list: list) -> list:
    """Уникализация списка
    :param _list: Список
    :return: list
    """
    unique = []
    unique_set = set(_list)
    for item in unique_set:
        unique.append(item)

    return unique


def get_module_name(path: str) -> str:
    """Извлечь имя модуля
    :param path: Полное имя модуля
    :return: str
    """
    try:
        index = path.index(".")
    except ValueError:
        index = len(path)

    return path[:index]


def file_get_contents(filename):
    """Прочесть содержимое файла
    :param filename: Путь к файлу
    :return: str
    """
    if not os.path.exists(filename):
        return None

    with open(filename) as f:
        return f.read()


def data_get(dictionary: dict, keys: str, default=None):
    """dot.notation доступ к атрибутам словаря
    :param dictionary: Словарь
    :param keys: Путь
    :param default: Значение по-умолчанию
    :return: mixed
    """

    def get_data(d, key):
        if isinstance(d, dict) and key:
            return d.get(key, default)
        elif isinstance(d, list) and key:
            key = int(key)
            return d[key] if d[key] else default
        else:
            return default

    return reduce(lambda d, key: get_data(d, key), keys.split("."), dictionary)


def recursive_find_by_key(obj, key):
    """Рекурсивный поиск значения по ключу в словаре
    :param obj: Словарь
    :param key: Ключ
    :return: mixed
    """
    if key in obj:
        return obj[key]

    for k, v in obj.items():
        if isinstance(v, dict):
            item = recursive_find_by_key(v, key)
            if item is not None:
                return item


def replace_in_file(file, needle: str, replacement: str):
    """Заменить вхождение в файле
    :param file: Путь к файлу
    :param needle: Что ищем
    :param replacement: На что заменить
    :return: bool
    """
    if not os.path.exists(file):
        return False

    with open(file, "r+") as f:
        content = f.read()
        new_content = re.sub(needle, str(replacement), content, flags=re.IGNORECASE | re.MULTILINE)
        f.seek(0)
        f.write(new_content)
        f.truncate()

    return True


def get_landing_tpl_path() -> str:
    """Получение папки шаблона лэнда
    :return: str
    """
    tpl_path = settings().TEMPLATE_SITE

    if not tpl_path:
        landing = get_landing()
        tpl_path = landing.app_name

    return str(tpl_path)


def is_content_manager(user):
    """Пользователь контентщик?"""
    return user.in_group("Контентщик") or user.in_group("Программист") or user.is_superuser


def is_integrator(user):
    """Пользователь интегратор?"""
    return user.in_group("Интегратор")


def add_elist_to_globals(landing: Landing, elist_instance: EditableList, local_data=None):
    """Добавление elist в GLOBAL_VARS"""
    for id, elem in elist_instance.instances.items():
        elist_name = str(elem).replace(landing.domain, "").strip()
        if local_data and elist_name in local_data:
            elist_instance.instances[elist_name] = local_data[elist_name]
        else:
            elist_instance.instances[elist_name] = elem

    GLOBAL_VARS[get_current_host(landing)][f"elist_{landing.app_name}"] = elist_instance


def merge_urls(landing_urls):
    """Мердж роутов
    :param landing_urls: list Список роутов лэндинга
    :return: list
    """
    from core.urls import urlpatterns as core_urlpatterns

    urlpatterns = []
    for url_pattern in landing_urls:
        for core_url_pattern in core_urlpatterns:
            if str(url_pattern.pattern) == str(core_url_pattern.pattern):
                urlpatterns.append(url_pattern)
            else:
                urlpatterns.append(core_url_pattern)

    return urlpatterns


def make_img_plug(name, width, height, module_path=None, custom_plug=None):
    """Генерируем плейсхолдер для изображения, если никакого не нашли
    :param name: Имя изображения
    :param width: Ширина
    :param height: Высота
    :param module_path: Папка модуля
    :param custom_plug: Кастомное название для файла plug
    :return:
    """

    filename, file_extension = os.path.splitext(name)

    if name.endswith((".jpg", ".jpeg", ".webp", ".svg")):
        name = name.replace(str(file_extension), ".png")

    if custom_plug:
        path = settings().MEDIA_ROOT / f"{module_path}/{name}"
        src = f"{settings().MEDIA_URL}{module_path}/{name}"
    else:
        path = settings().MEDIA_ROOT / name
        src = f"{settings().MEDIA_URL}{name}"

    if custom_plug:
        plug_name = f"{settings().BASE_DIR}/media/plugs/{width}X{height}_{custom_plug}.png"
        plug_src = f"{MEDIA_URL}plugs/{width}X{height}_{custom_plug}.png"
        not_found_image = f"{custom_plug}-not-found.png"
    else:
        plug_name = f"{settings().BASE_DIR}/media/plugs/{width}X{height}.png"
        plug_src = f"{MEDIA_URL}plugs/{width}X{height}.png"
        not_found_image = "image-not-found.png"

    if not os.path.exists(path) or not os.path.isfile(src):
        media_plugs = settings().BASE_DIR / "media/plugs"

        if not os.path.exists(media_plugs):
            os.makedirs(media_plugs, exist_ok=True)

        if not os.path.isfile(plug_name):
            # Создание фона
            background = Image.new("RGB", (int(width), int(height)), (241, 241, 241))

            # Открытие и изменение размера изображения
            img = Image.open(settings().BASE_DIR / f"resources/{not_found_image}", "r").convert("RGBA")

            new_width = min(int(width) // 2, 40)
            new_height = min(int(height) // 2, 40)

            # Изменяем размер изображения
            img_resized = img.resize((new_width, new_height))

            # Вычисление смещения для вставки изображения по центру
            bg_width, bg_height = background.size
            img_width, img_height = img_resized.size

            offset = ((bg_width - img_width) // 2, (bg_height - img_height) // 2)

            # Вставка изображения по центру фона
            background.paste(img_resized, offset, img_resized)

            # Добавление рамки к фону
            background = ImageOps.expand(background, border=1, fill="#d9d6d6")

            # Сохранение результата
            background.save(plug_name)

    return plug_src


def get_module_from_context(context) -> str:
    """Получить имя модуля
    :return: str
    """
    module = context.get("current_module")

    if not module:
        result = re.search(r"(^|modules\/)(m-.+?)\/", context.get("template_name"))

        if result:
            return result.group(2)

    return module


def module(name, file, universal, variables=None):
    """Подключаем модуль
    :param name: Имя модуля
    :param file: Имя файла
    :param variables: Переменные
    :return:
    """
    if variables is None:
        variables = {}

    request = get_request()
    utm_field = get_landing().utm_campaign
    ab_field = get_landing().ab_test
    tpl_path = get_landing_tpl_path()
    app_name = get_landing().app_name
    ab_test_excluded = get_ab_test_excluded_modules()
    b_file_path = settings().BASE_DIR / f"modules/{name}/{tpl_path}/{file}-b.html"
    b_landing_file_path = settings().BASE_DIR / f"modules/{name}/{app_name}/{file}-b.html"

    variables["current_module"] = name

    if is_ab_test() and name in ab_test_excluded:
        return render_to_string(
            f"{name}/{tpl_path}/{file}.html",
            variables,
            request=request,
        )

    if is_ab_test() and get_version(request, utm_field, ab_field) == "b" and os.path.exists(b_landing_file_path):
        return render_to_string(
            f"{name}/{app_name}/{file}-b.html",
            variables,
            request=request,
        )
    elif is_ab_test() and get_version(request, utm_field, ab_field) == "b" and os.path.exists(b_file_path):
        return render_to_string(
            f"{name}/{tpl_path}/{file}-b.html",
            variables,
            request=request,
        )

    if universal == True:
        path = f"{name}/{file}.html"
    else:
        path = f"{name}/{tpl_path}/{file}.html"

    try:
        return render_to_string(
            path,
            variables,
            request=request,
        )
    except ImportError:
        pass

    return render_to_string(
        path,
        variables,
        request=request,
    )


def get_client_ip(request):
    """Получить IP клиента"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def get_client_phone(request):
    return request.session.get("client_phone", "")


def recursive_replace(data, needle, replace):
    """Рекурсивная замена"""
    if isinstance(data, dict):
        return {k: recursive_replace(v, needle, replace) for k, v in data.items()}
    elif isinstance(data, list):
        return [recursive_replace(i, needle, replace) for i in data]
    else:
        if needle is None:
            return replace if data is None else data
        if needle is True:
            return replace if data is True else data
        if needle is False:
            return replace if data is False else data

        return replace if data == needle else data


def clear_landing_cache(landing=None, with_globals=False) -> bool:
    """Удаление кэша представления"""
    enable_cache = int(os.environ.get("ENABLE_CACHE", default=0))

    if not enable_cache:
        return True

    landing = landing if landing else get_landing()
    keys = cache.keys(f"{landing.app_name}|*")
    host_key = get_current_host(landing)
    chunks = get_chunks() if get_chunks() else get_chunks(landing)

    if len(keys):
        for key in keys:
            cache.delete(key)

        if with_globals and host_key in GLOBAL_VARS:
            if chunks:
                del GLOBAL_VARS[host_key][f"chunks_{landing.app_name}"]

            if get_elist(landing):
                del GLOBAL_VARS[host_key][f"elist_{landing.app_name}"]

        return True

    return False


def cached_page(view=None, key=None):
    """Кэш страницы"""
    key = key if key else cache_key(view if view else view_name())

    return cache.get(key)


def hash_string(string):
    """Хэширование строки"""
    import hashlib

    string = string if isinstance(string, str) else ""

    return hashlib.md5(string.encode("utf-8")).hexdigest()


def cache_key(view=None, request=None):
    """Получить префикс кэша"""
    # @TODO ограничивать по группе лэнда?
    from core.templatetags.core_tags import offer_end_time, is_working_time

    request = request if request else GLOBAL_VARS.get(get_current_host(), {}).get("request")
    user_scope = "staff" if request.user.is_staff else "user"
    view = view if view else view_name()
    get_version_salt = None
    landing = get_landing()
    utm_field = landing.utm_campaign if landing else None
    ab_field = landing.ab_test if landing else None
    if is_ab_test():
        get_version_salt = get_version(request, utm_field, ab_field)

    salt = (
        f"is_working_time_new={is_working_time(with_elist=True)}|is_working_time={is_working_time()}"
        f"|ab_test_checker={is_ab_test()}|tag_ab_version_a=a|tag_ab_version_b=b|ab_test={get_version_salt}"
        f"|new_year={is_new_year()}|offer_end_time={offer_end_time()}|moderate={on_moderation()}"
        f"|check_holidays={is_holidays()}|offer_end_time={offer_end_time()}|moderate={on_moderation()}"
        f"|hide_copyright={hide_copyright()}|is_b_version={is_b_version()}|user_is_fraud_by_ip={user_is_fraud(request, check_type='ip')}"
        f"|send_quiz_in_albato={send_quiz_in_albato()}"
    )

    if type(landing) is Landing:
        landing_cache_module = importlib.import_module(f"_sites.{landing.app_name}.cache")
        scoped_salt = f"scoped_salt:{landing_cache_module.get_cache_salt(request)}"

        hashed_salt = f"{landing.app_name}|{view}|salt:{user_scope}:{hash_string(salt + scoped_salt)}"
    else:
        hashed_salt = f"no_landing|{view}|salt:{hash_string(user_scope + salt)}"

    return hashed_salt


def view_name(request=None):
    """Имя текущего view"""
    request = request if request else GLOBAL_VARS.get(get_current_host(), {}).get("request")

    return request.resolver_match.view_name.split(".")[-1]


def cache_page(*args, **kwargs):
    """Кэширование страницы"""
    from django.core.cache.backends.base import DEFAULT_TIMEOUT
    from functools import wraps

    enable_cache = int(os.environ.get("ENABLE_CACHE", default=0))

    def real_decorator(function):
        cache_ttl = getattr(settings(), "CACHE_TTL", DEFAULT_TIMEOUT)
        view = function.__name__

        @wraps(function)
        def wrapper(*args, **kwargs):
            path = kwargs.get("path")

            if not enable_cache:
                if is_dev():
                    color_print("Cache was disabled in .env file", "ENABLE_CACHE=0")

                return function(*args, **kwargs)

            request = args[0]
            key = cache_key(view if not path else path, request)

            # Дополнительные ключи кэша из параметров запроса
            white_query_keys = settings().WHITE_QUERY_KEYS
            if len(white_query_keys):
                query_string = {x[0]: x[1] for x in [x.split("=") for x in request.META.get("QUERY_STRING", "")[1:].split("&")]}
                query_salt = ""
                for query_key, query_value in query_string.items():
                    if query_key in white_query_keys:
                        query_salt += f"{query_key}|{query_value}"

                if len(query_salt):
                    key += f"|query:{hash_string(query_salt)}"

            html = cached_page(view=view if not path else path, key=key)

            if html:
                # Проверяем и чистим битый кэш для админа
                if is_content_manager(request.user) and not ('class="admin-panel"' in str(html.content)):
                    html = None

                # Достаём кэш для админа без права на редактирование, но с панелью админа
                if ("staff" in key) and is_integrator(request.user):
                    key = key.replace("staff", "integrator")
                    html = cached_page(view=view if not path else path, key=key)

                # Достаём кэш для админа без права на редактирование
                if ("staff" in key) and not is_content_manager(request.user) and not is_integrator(request.user):
                    key = key.replace("staff", "user")
                    html = cached_page(view=view if not path else path, key=key)

                # Проверяем и чистим битый кэш для пользователя
                if html and not is_content_manager(request.user) and ('class="admin-panel"' in str(html.content)):
                    html = None

                if html and is_dev():
                    color_print("Return cached page", key)

                if html:
                    return html

            html = function(*args, **kwargs)

            # Проверяем и сохраняем кэш для админа
            if ("staff" in key) and not is_integrator(request.user) and ('class="admin-panel"' in str(html.content)):
                cache.set(key, value=html, timeout=cache_ttl)
            # Проверяем и сохраняем кэш для админа без права на редактирование, но с панелью админа
            elif ("staff" in key) and is_integrator(request.user) and ('class="admin-panel"' in str(html.content)):
                key = key.replace("staff", "integrator")
                cache.set(key, value=html, timeout=cache_ttl)
            # Проверяем и сохраняем кэш для админа без права на редактирование
            elif ("staff" in key) and not is_content_manager(request.user) and not ('class="admin-panel"' in str(html.content)):
                key = key.replace("staff", "user")
                cache.set(key, value=html, timeout=cache_ttl)
            # Проверяем и сохраняем кэш для пользователя
            elif ("user" in key) and not ('class="admin-panel"' in str(html.content)):
                cache.set(key, value=html, timeout=cache_ttl)

            if is_dev():
                color_print("Create page cache", key)

            return html

        return wrapper

    return real_decorator


def escape_markdown(text, *, as_needed=False, ignore_links=True, exclude_chars=None):
    """Эскейпинг разметки markdown с возможностью исключений для некоторых символов."""
    markdown_chars = ["*", "`", "_", "~", "|"]

    if exclude_chars:
        markdown_chars = [c for c in markdown_chars if c not in exclude_chars]

    sub_regex = "|".join(r"\{0}(?=([\s\S]*((?<!\{0})\{0})))".format(c) for c in markdown_chars)
    common_regex = r"^>(?:>>)?\s|\[.+\]\(.+\)"

    escape_regex = re.compile(r"(?P<markdown>%s|%s)" % (sub_regex, common_regex))

    text = str(text)

    if not as_needed:
        url_regex = r"(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])"

        def replacement(match):
            group_dict = match.groupdict()
            is_url = group_dict.get("url")

            if is_url:
                return is_url

            return "\\" + group_dict["markdown"]

        dynamic_chars_regex = "|".join([re.escape(c) for c in markdown_chars])
        regex = r"(?P<markdown>[%s\\]|%s)" % (dynamic_chars_regex, common_regex)

        if ignore_links:
            regex = "(?:%s|%s)" % (url_regex, regex)

        return re.sub(regex, replacement, text)
    else:
        text = re.sub(r"\\", r"\\\\", text)

        return escape_regex.sub(r"\\\1", text)


def color_print(prefix, text):
    """Цветной вывод"""
    blue = "\033[94m"
    green = "\033[92m"
    end = "\033[0m"
    bold = "\033[1m"

    print(f"{blue}{bold}{prefix}{end} => {green}{text}{end}")


def images_is_different(image_1, image_2):
    """Изображения разные?"""
    from PIL import Image

    if not os.path.isfile(image_1) or not os.path.isfile(image_2):
        return True

    if image_1 == image_2:
        return False

    return list(Image.open(image_1).getdata()) == list(Image.open(image_2).getdata())


def convert_size(size_bytes):
    """Человекопонятный размер файла"""
    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_name[i]}"


def encode(text):
    """Кодирование текста из utf-8 в iso-8859-1"""
    return text.encode("utf-8").decode("iso-8859-1")


def send_to_albato(phone, name, quiz, wheel, url_page):
    """Отправка данных в Альбато"""
    from telegram.utils.bot import Telegram

    landing = get_landing()
    webhook = landing.albato_webhook if landing else None
    phone = int(re.sub(r"\D", "", str(phone)))
    domain = landing.domain

    if landing.send_quiz_in_albato:
        if not quiz:
            return False

    if not name:
        name = "Имя не задано"

    headers = {
        "Content-Type": "application/json;",
    }

    payload = {
        "phone": f"{phone}",
        "domain": f"{domain}",
        "source": f"{url_page}",
        "name": f"{name}",
    }

    if quiz:
        payload["quiz"] = f"{quiz}"
    elif wheel:
        payload["wheel"] = f"{wheel}"
    else:
        payload["quiz"] = "Заполнена простая форма, без квиза"

    if webhook:

        result = requests.post(webhook, headers=headers, data=json.dumps(payload))

        if (result.status_code < 200) or (result.status_code > 204):
            Telegram(chat_id="system").send_message(
                f"""🔴 *Django Landings - модуль Albato*: Ошибка отправки заявки!
*Лэндинг*: *{get_landing().domain}*
*Ошибка*: {escape_markdown(result)}"""
            )
            return False

    return False


def get_fraud_list(base_name):
    """Получить базу, если нет или устарела"""
    url = f"https://antispam-data.hb.ru-msk.vkcs.cloud/{base_name}.json"
    file_path = BASE_DIR / f"antifraud/data/{base_name}.json"
    file_is_stale = False

    if os.path.exists(file_path):
        file_updating_date = os.path.getmtime(file_path)
        now = int(time.time())
        file_age = now - file_updating_date
        file_is_stale = file_age > (1 * 24 * 60 * 60)

    if not os.path.exists(file_path) or file_is_stale:
        downloaded_data = requests.get(url)

        if downloaded_data.ok:
            data_json = downloaded_data.json()
            with open(file_path, "w") as json_file:
                json.dump(data_json, json_file)

            return True

    return False


def user_is_fraud(request, check_type=None, param_value=None):
    """Пользователь бот?"""

    if not on_antispam():
        return False

    match check_type:
        case "ip":
            base_name = "spam_ip_addresses"
            param_name = "ip"
            param_value = get_client_ip(request)
        case "ya_id":
            base_name = "spam_id_yandex_metrica"
            param_name = "yaClientId"
        case "user_phone":
            base_name = "spam_phones"
            param_name = "phone"
        case _:
            return False

    file_path = BASE_DIR / f"antifraud/data/{base_name}.json"

    get_fraud_list(base_name)

    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as json_file:
            json_data = json.load(json_file)
            for item in json_data:
                if item[param_name] == param_value:
                    request.session["antifraud"] = param_name
                    return True

    return False


def field_to_end(fields, key, exception: list = []):
    """Перемешает поле админ формы в конец"""
    if key in fields:

        if exception and key in exception:
            fields.remove(key)
        else:
            fields.remove(key)
            fields.append(key)


def is_dev():
    """Это dev среда?"""
    return ENVIRONMENT == "dev"


def is_prod():
    """Это prod среда?"""
    return ENVIRONMENT == "prod"


def login_as(request, email: str):
    """Войти по Email пользователя"""
    from django.contrib.auth import login
    from django.contrib.auth.models import User

    user = User.objects.filter(email=email).first()

    if user:
        login(request, user)


def is_valid_uuid(uuid_to_test, version=4):
    """Проверка UUID"""
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


def get_causer():
    """Получить пользователя запроса"""
    try:
        for frame_record in inspect.stack():
            if frame_record[3] == "get_response":
                return frame_record[0].f_locals["request"].user
    except:
        return None

    return None


def converted_image(file, input_extension=None, target_extension=None, quality: int = None):
    """Сжатие или конвертация изображения"""
    allowed_extensions = ("jpg", "jpeg", "png", "webp", "heic", "svg")
    input_extension = input_extension if input_extension in allowed_extensions else None
    input_extension = "jpeg" if input_extension == "jpg" else input_extension

    target_extension = target_extension if target_extension in allowed_extensions else None
    target_extension = "jpeg" if target_extension == "jpg" else target_extension

    if quality:
        quality = int(quality)

    save_options = {
        "quality": quality if quality and 0 <= quality <= 100 else 80,
        "lossless": False,
        "optimize": True,
        "progressive": True,
    }

    _, file_extension = os.path.splitext(file)
    file_extension = file_extension.lower()

    file_extension = file_extension.lstrip(".")
    file_extension = "jpeg" if file_extension == "jpg" else file_extension

    if file_extension == "svg":
        target_extension = "svg"

    if input_extension:
        if file_extension == input_extension:
            return converted_process(file, target_extension, save_options)
    elif file_extension in allowed_extensions:
        return converted_process(file, target_extension, save_options)
    else:
        return {"success": False, "error": f"Загружен недопустимый формат файла - {file_extension}"}


def converted_process(file=None, target_extension=None, save_options=None):

    def save_with_check(image_format):
        """Сохраняет с исходным названием и указанным форматом, проводя проверку уменьшения файла"""
        original_size = os.path.getsize(file)
        temp_file = file + "_temp"

        if image_format.lower() == "webp" and len(ImageSequence.all_frames(image)) > 1:
            save_options_with_animation = {"save_all": True}
            image.save(temp_file, image_format, **save_options_with_animation)
        else:
            image.save(temp_file, image_format, **save_options)

        if os.path.getsize(temp_file) < original_size:
            os.replace(temp_file, file)
        else:
            os.remove(temp_file)

    if target_extension == "svg":

        path = Path(file)
        path.write_text(scourString(path.read_text()))

        return file

    try:
        pillow_heif.register_heif_opener()
        with Image.open(file) as image:
            converted_file_name = None

            if target_extension:
                file_name, file_extension = os.path.splitext(file)
                converted_file_name = file.replace(file_extension, f".{target_extension}")

                if target_extension == "webp":
                    if not file_extension == ".webp":
                        image.save(converted_file_name, "webp", **save_options)
                        os.remove(file)
                    else:
                        if len(ImageSequence.all_frames(image)) > 1:
                            save_options_with_animation = {"save_all": True}
                            image.save(converted_file_name, target_extension, **save_options_with_animation)
                        else:
                            image.save(converted_file_name, target_extension, **save_options)

                elif target_extension == "heic":
                    if not file_extension == ".heic":
                        image.save(converted_file_name, "heif", **save_options)
                        os.remove(file)
                    else:
                        image.save(converted_file_name, target_extension, **save_options)
                else:
                    if image.format == "PNG" or image.mode == "RGBA":
                        image = image.convert("RGB")
                        image.save(converted_file_name, target_extension, **save_options)
                    else:
                        image.save(converted_file_name, target_extension, **save_options)

                    if converted_file_name != file:
                        os.remove(file)

                    if target_extension == "jpeg":
                        os.rename(converted_file_name, file_name + ".jpg")
                        converted_file_name = file_name + ".jpg"

            elif image.format == "WEBP" or image.format == "JPEG":
                save_with_check(image.format)
            elif image.format == "HEIF":
                save_with_check(image.format)
            elif image.format == "PNG" and image.mode == "RGBA":
                if not any(pixel[3] < 255 for pixel in image.getdata()):
                    image = image.convert("RGB")
                    save_with_check("JPEG")
                else:
                    if save_options["quality"] <= 50:
                        image = image.convert("P", palette=Image.ADAPTIVE, dither=Image.FLOYDSTEINBERG)
                    else:
                        reduce_factor = 8 if save_options["quality"] <= 69 else (4 if save_options["quality"] <= 85 else 2)
                        channels = [channel.point(lambda i: i // reduce_factor * reduce_factor) for channel in image.split()]
                        channels[3] = channels[3].point(lambda i: i // 4 * 4)
                        image = Image.merge("RGBA", channels)
                    save_with_check("PNG")

            return converted_file_name if converted_file_name else file

    except IOError as e:
        print(f"Ошибка при обработке файла {file}: {e}")
        return f"Ошибка при обработке файла {file}: {e}"


def check_raster_svg(image, is_svg=False):
    """Проверка SVG на растр внутри"""
    _, file_extension = os.path.splitext(str(image))
    svg_check = (
        file_extension == ".svg" or file_extension == ".svg+xml" or str(image).find(".svg") != -1 or str(image).find(".svg+xml") != -1
    )

    if is_svg or svg_check:
        svg_code = image.read().rstrip().decode("utf-8").lower()
        if svg_code.find("base64") != -1:
            image.seek(0)
            return True

    image.seek(0)
    return False


def exec_command(command: str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    command = command if shell else command.split()
    process = subprocess.Popen(command, shell=shell, stdout=stdout, stderr=stderr, text=True)
    result, error = process.communicate()

    if error:
        return False, error.encode("utf-8", errors="replace").decode("utf-8").strip()

    return True, result.encode("utf-8", errors="replace").decode("utf-8").strip()


def get_file_hash(file_path):
    import hashlib

    with open(file_path, "rb") as f:
        hash_obj = hashlib.sha256()
        while chunk := f.read(4096):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def get_var_params(file_path):
    params = []

    # Чтение файла
    with open(file_path, "r") as file:
        css_text = file.read()

    matches = re.findall(r":root\s\{([^}]+)\}", css_text)

    if not matches:
        matches = re.findall(r":root\{([^}]+)\}", css_text)

    if matches:
        for line in matches[0].splitlines():
            if len(line) > 1:
                params.append(line)

        root_params = "\n".join(params)

        root_blank = f":root {{\n{root_params}\n}}"

        return root_blank


def update_vars_params(file_path, params):
    get_vars = get_var_params(file_path)

    if get_vars is not None:
        check_vars = re.findall(r"--[^:]+: [^;]+;", get_vars)
        cloud_vars = re.findall(r"--[^:]+: [^;]+;", params)

        check_vars_dict = {line.split(":")[0].strip(): line for line in check_vars}
        cloud_vars_dict = {line.split(":")[0].strip(): line for line in cloud_vars}

        for key, value in check_vars_dict.items():
            cloud_vars_dict[key] = value

        updated_vars = "\n  ".join(cloud_vars_dict.values())

        root_block = f":root {{\n  {updated_vars}\n}}"

        return root_block


def find_media_dirs(app_name, is_files=False):
    from core.settings import MEDIA_ROOT
    import os

    media_dirs_set = set()

    for root, dirs, files in os.walk(os.path.join(MEDIA_ROOT, app_name), topdown=True):

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)

            if "/uploaded" not in dir_path:
                relative_dir = dir_path.replace(os.path.join(MEDIA_ROOT, app_name), "").lstrip(os.path.sep)
                media_dirs_set.add((relative_dir, relative_dir))

        if is_files:
            for file_name in files:
                file_path = f"{root}/{file_name}"
                file_value = file_path.replace(os.path.join(MEDIA_ROOT, app_name), "").lstrip(os.path.sep)
                media_dirs_set.add((file_value, file_value))

    media_dirs_arr = sorted(list(media_dirs_set))

    media_dirs_arr.insert(0, ("false", "Значение не выбрано"))

    if not is_files:
        media_dirs_arr.append(("other", "Другой модуль"))
    else:
        if len(media_dirs_arr) > 1:
            media_dirs_arr.insert(1, ("all", "Удалить всю папку c картинками"))

    return media_dirs_arr


def get_ab_test_excluded_modules(landing=None):
    """Получить модули, исключенные из A/B тестирования"""
    landing = landing if landing else get_landing()

    if not landing or not landing.ab_test_excluded_modules:
        return list()

    return landing.ab_test_excluded_modules.splitlines()


def update_config_husky(variable, value, env_file=".husky/config.json"):
    os.makedirs(os.path.dirname(env_file), exist_ok=True)

    """Если файл не существует, создать его с пустым JSON объектом"""
    if not os.path.isfile(env_file):
        os.chmod(".husky/pre-commit", 0o555)
        os.chmod(".husky/pre-push", 0o555)
        with open(env_file, "w") as file:
            json.dump({}, file)

    os.chmod(env_file, 0o666)

    with open(env_file, "r") as file:
        data = json.load(file)

    data[variable] = value

    with open(env_file, "w") as file:
        json.dump(data, file, indent=4)

    # Файлы, которые должны быть исполняемыми
    files_to_make_executable = [".husky/pre-commit", ".husky/pre-push"]

    for filename in files_to_make_executable:
        if os.path.isfile(filename):
            st = os.stat(filename)
            os.chmod(filename, st.st_mode | stat.S_IEXEC)

    os.chmod(env_file, 0o444)


def get_policy_text(landing=None):
    """Получить текст Политики конфиденциальности"""
    landing = landing if landing else get_landing()

    return landing.conditions_text if landing else False


def is_policy_file(landing=None):
    """Проверяет наличие файла Политики конфиденциальности"""
    from core.settings import MEDIA_ROOT

    landing = landing if landing else get_landing()

    if landing:
        policy_pdf = str(landing.conditions_pdf).split("/")[-1] if landing.conditions_pdf else None
        if policy_pdf and os.path.isfile(f"{MEDIA_ROOT}/{landing.app_name}/{policy_pdf}"):
            return True
    return False


def enable_local_data(request, path):

    local_data_path = request.session.get("usage_local_data") if "usage_local_data" in request.session else None

    if local_data_path and local_data_path == str(path).strip("/"):
        return True
    else:
        return False


def find_files_app(blank=False):
    """Ищет директорию app
    :param blank: Найти директорию шаблона?
    """

    landing = get_landing().domain
    app_name = landing.replace("-", "_").replace(".", "__")

    if blank:
        try:
            app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")
            page_template = app_settings_template.TEMPLATE_SITE or app_name
        except (ImportError, AttributeError):
            page_template = app_name if "__blank__sinergium" in app_name else None
    else:
        return app_name

    return page_template


def pages_list():
    landing = get_landing()
    pages = Page.objects.filter(landing_id=landing.id).all()
    links = []
    for page in pages:
        links.append(page.path)
    elist_policy = EditableList(landing).get_instance("policy")
    if elist_policy:
        links.append("policy")
    links.append("404")

    return links


def compile_custom_styles(landing: Class = None, custom_styles: str = None) -> None | str:
    """Компиляция кастомного scss"""
    landing = landing if landing else get_landing()

    sheets = custom_styles if custom_styles else landing.custom_scss if landing else None

    if not sheets:
        return None

    try:
        compiled_stylesheet = sass.compile(string=landing.custom_scss, output_style="compressed")
    except sass.CompileError:
        return None

    if isinstance(compiled_stylesheet, str):
        formatted_value = re.sub(r"/\*.*?\*/", "", compiled_stylesheet, flags=re.DOTALL)
        formatted_value = re.sub(r"^\s+", "", formatted_value, flags=re.MULTILINE)
        formatted_value = re.sub(r"^\s*[\r\n]+", "", formatted_value, flags=re.MULTILINE)
        formatted_value = re.sub(r"\s+", " ", formatted_value)
        formatted_value = re.sub(r"\s*([{};,:])\s*", r"\1", formatted_value)

        return formatted_value.strip()

    return None
