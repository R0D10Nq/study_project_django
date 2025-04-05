from PIL import Image
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.template.exceptions import TemplateDoesNotExist
from abtest.helpers import get_version
from core.chunks.helpers import admin_chunk_wrapper, chunk as core_chunk, search_existing_chunk
from core.helpers import (
    find_files_app,
    get_current_page,
    pages_list,
    settings,
    get_landing_data,
    get_landing,
    get_request,
    get_landing_tpl_path,
    is_dev,
    is_prod,
    env,
    make_img_plug,
    data_get,
    get_module_from_context,
    module as core_module,
    get_client_ip,
    view_name as core_view_name,
    on_moderation,
    is_new_year as new_year,
    get_client_phone,
    get_current_host as core_get_current_host,
    get_elist,
    add_elist_to_globals,
    is_policy_file,
    is_content_manager,
)
from core.models import Chunk, EList, Page
from core.settings import BASE_DIR, DISABLED_KEY
from core.models import EList, Page
from core.settings import BASE_DIR
from core.utils.elist import EditableList
from core.data import GLOBAL_VARS
from plural.templatetags.plural_filters import plural
from bs4 import BeautifulSoup
import os, json, re, ast, datetime, math, pytz, time, calendar, base64, importlib

register = template.Library()


@register.simple_tag(takes_context=True)
def define(context, value: str, default=None):
    """Тэг для объявления переменных
    :param context:
    :param value: Значение переменной
    :param default: Значение по-умолчанию
    :return: mixed
    """
    if not value:
        return default

    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except Exception:
            if value.startswith("data:"):
                global_data = get_landing_data()
                value = data_get(global_data, value.replace("data:", ""))
            elif value.endswith(".html"):
                try:
                    landing_tpl_path = get_landing_tpl_path()
                    module = get_module_from_context(context)

                    if os.path.exists(settings().BASE_DIR / f"core/templates/common/modules/{module}/{landing_tpl_path}/{value}"):
                        view_way = f"common/modules/{module}/{landing_tpl_path}/{value}"
                    elif os.path.exists(settings().BASE_DIR / f"common/modules/{module}/{value}"):
                        view_way = f"common/modules/{module}/{value}"
                    else:
                        view_way = f"common/{value}"

                    value = render_to_string(view_way, {}, request=context.request)
                except TemplateDoesNotExist as e:
                    if is_dev():
                        raise TemplateDoesNotExist(str(e))

        return mark_safe(value) if isinstance(value, str) else value

    return mark_safe(value) if isinstance(value, str) else value


@register.simple_tag(takes_context=True)
def svg(context, *args, **kwargs) -> bool | str:
    """Тэг для вставки svg
    :param context: Контекст
    :return: str
    """

    from core.chunks.queries.chunk import ChunkQuery

    name = args[0] + ""
    module = value = None
    this_plug = False
    width = kwargs.get("width")
    height = kwargs.get("height")
    is_elist = kwargs.get("is_elist")
    is_slider = kwargs.get("is_slider")
    is_swiper = kwargs.get("is_swiper")
    img_template = "common/img.html"

    if not width and not height:
        kwargs["width"] = width = 50
        kwargs["height"] = height = 50

    if name.endswith(".svg"):

        try:

            if kwargs.get("without_lazy"):
                img_template = "common/img_without_lazy.html"

            module = (
                get_module_from_context(context)
                if kwargs.get("module") == "common" or not kwargs.get("module")
                else kwargs.get("module") + ""
            )

            existing = get_image_src(args, kwargs, no_plugs=True)
            landing_media_dir = str(settings().MEDIA_ROOT / module)

            if (
                not os.path.exists(f"{settings().BASE_DIR}{existing}")
                and not os.path.exists(landing_media_dir + "/" + name)
                and not os.path.exists(settings().MEDIA_ROOT / "common" / name)
                and settings().MEDIA_ROOT / name
            ):

                this_plug = True
                if width and height:
                    plug = make_img_plug(name, width, height, module, custom_plug="svg")
                    value = render_to_string(
                        img_template,
                        {
                            "media_src": plug,
                            "width": width,
                            "height": height,
                            "is_slider": is_slider,
                            "is_swiper": is_swiper,
                            "is_elist": is_elist,
                            "attributes": kwargs,
                            "module": module,
                        },
                        request=get_request(),
                    )
                else:
                    plug = make_img_plug(name, 100, 100, module, custom_plug="svg")
                    value = render_to_string(
                        img_template,
                        {
                            "media_src": plug,
                            "width": width,
                            "height": height,
                            "is_slider": is_slider,
                            "is_swiper": is_swiper,
                            "is_elist": is_elist,
                            "attributes": kwargs,
                            "module": module,
                        },
                        request=get_request(),
                    )

            if not existing:
                existing = name

                if not this_plug:
                    if os.path.exists(landing_media_dir + "/" + name):
                        with open(landing_media_dir + "/" + name, "r") as file:
                            value = file.read().rstrip()
                    elif os.path.exists(settings().MEDIA_ROOT / "common" / name):
                        with open(settings().MEDIA_ROOT / "common" / name, "r") as file:
                            value = file.read().rstrip()
                    else:
                        with open(settings().MEDIA_ROOT / name, "r") as file:
                            value = file.read().rstrip()
            if not is_elist and not this_plug:
                ChunkQuery.save(name=name, content=existing.replace(f"/media/{get_landing().app_name}/", ""))

            if existing and not this_plug:
                if os.path.exists(f"{settings().BASE_DIR}{existing}"):
                    with open(f"{settings().BASE_DIR}{existing}", "r") as file:
                        value = file.read().rstrip()

            if len(kwargs) and not this_plug:
                value = BeautifulSoup(value, features="html.parser")
                for attribute_name, attribute_value in kwargs.items():
                    if not value.find("svg").get(f"{attribute_name}"):
                        value.find("svg")[f"{attribute_name}"] = attribute_value
                    else:
                        value.find("svg")[f"{attribute_name}"] = f"{value.find('svg').get(f'{attribute_name}')} {attribute_value}"

        except Exception:
            if is_dev():
                raise Exception(f"SVG error {name}!!!")
            value = ""

    return admin_chunk_wrapper(name, mark_safe(str(value)), module, is_img=True) if not is_elist else mark_safe(str(value))


@register.simple_tag(takes_context=True)
def img_src(context, name: str, is_exist=False, module=None, width=None, height=None):
    """Получить ссылку на изображение
    :param context:
    :param name: Путь к изображению
    :param module: Модуль изображения
    :param width: Ширина превью
    :param height: Высота превью
    :return: str
    """
    src = None

    if is_dev or name is not None:
        name += ""
    else:
        name = "plug.png"

    module = module if module else get_module_from_context(context)

    if module:
        if os.path.exists(settings().MEDIA_ROOT / f"{module}/{name}"):
            src = f"{settings().MEDIA_URL}{module}/{name}"
    else:
        if os.path.exists(settings().MEDIA_ROOT / name):
            src = f"{settings().MEDIA_URL}{name}"

    if not src:
        if is_exist:
            return "does_not_exist"
        if width and height:
            src = make_img_plug(name, width, height, module)
        else:
            src = make_img_plug(name, 100, 100, module)

    return src


def get_image_src(args, kwargs, no_plugs=None, custom_plug=None):
    name = args[0] + ""
    width = kwargs.get("width")
    height = kwargs.get("height")
    module = kwargs.get("module")
    is_elist = kwargs.get("is_elist")
    allowed_extensions = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp")
    allowed_extensions_video = (".mp4", ".webm")
    media_root = settings().MEDIA_ROOT
    media_url = settings().MEDIA_URL
    src = None
    page = get_current_page()

    if not is_elist and (not width or not height):
        raise Exception("Укажите ширину и высоту изображения")

    if width:
        del kwargs["width"]

    if height:
        del kwargs["height"]

    if kwargs.get("template"):
        del kwargs["template"]

    if module:
        del kwargs["module"]

    existing = search_existing_chunk(name)

    if existing:
        if not is_elist:
            if not existing.through and existing.custom_content and page and existing.custom_content.get(str(page.id), None):
                path = existing.custom_content.get(str(page.id), None)
            elif not existing.through and page:
                path = existing.custom_content.get(str(page.id), None)
            else:
                path = existing.content
        else:
            path = existing.content
    else:
        path = name

    if not path:
        return None

    _, file_extension = os.path.splitext(path)

    if not existing and file_extension not in allowed_extensions and file_extension not in allowed_extensions_video:
        # Ищем в данных, если нет ещё чанка
        global_data = get_landing_data()
        path = data_get(global_data, name)

        if path:
            _, file_extension = os.path.splitext(path)
        else:
            return "Не указана картинка!"

        if file_extension not in allowed_extensions and file_extension not in allowed_extensions_video:
            raise Exception(f"Неизвестный формат изображения для {path}!")

    if os.path.isfile(media_root / "common" / path):
        src = f"{media_url}common/{path}"

    elif os.path.isfile(media_root / f"{module}/common" / path):
        src = f"{media_url}{module}/common/{path}"

    elif os.path.isfile(media_root / path):
        src = f"{media_url}{path}"

    elif os.path.isfile(media_root / f"{module}/{path}"):
        src = f"{media_url}{module}/{path}"

    if not src and not no_plugs:
        if width and height:
            src = make_img_plug(name, width, height, module, custom_plug=custom_plug)
        else:
            src = make_img_plug(name, 100, 100, module, custom_plug=custom_plug)

    return src


@register.simple_tag(takes_context=True)
def img_src_empty(context, module=None):
    """Получить ссылку на изображение
    :param context:
    :param module: Модуль изображения
    """
    src = None
    module = module if module else get_module_from_context(context)

    if module:
        if os.path.exists(settings().MEDIA_ROOT / f"{module}/"):
            src = f"{settings().MEDIA_URL}{module}/"
    else:
        if os.path.exists(settings().MEDIA_ROOT):
            src = f"{settings().MEDIA_URL}"

    return src


@register.simple_tag
def src_placeholder(**kwargs):
    """Получить прозрачное превью изображения
    :param context: Контекст
    :return: str
    """

    width = str(kwargs.get("width"))
    height = str(kwargs.get("height"))

    image = (
        "<svg width='"
        + width
        + "' height='"
        + height
        + "' viewBox=\"0 0 "
        + width
        + " "
        + height
        + '" xmlns="http://www.w3.org/2000/svg">  <rect fill="transparent" width=\''
        + width
        + "' height='"
        + height
        + "' /></svg>"
    )

    return "data:image/svg+xml;base64," + base64.b64encode(bytes(image, "utf-8")).decode("utf-8")


@register.simple_tag(takes_context=True)
def img_tag(context, *args, **kwargs) -> str:
    """Получить тэг изображения
    :param context: Контекст
    :return: str
    """
    from core.chunks.queries.chunk import ChunkQuery

    name = args[0] + ""
    width = kwargs.get("width")
    height = kwargs.get("height")
    is_elist = kwargs.get("is_elist")
    is_slider = kwargs.get("is_slider")
    is_swiper = kwargs.get("is_swiper")
    module = kwargs.get("module") if kwargs.get("module") else get_module_from_context(context)
    kwargs["module"] = module
    src = get_image_src(args, kwargs)
    img_template = "common/img.html"

    if not kwargs.get("title"):
        kwargs["title"] = "Изображение"

    if not kwargs.get("alt"):
        kwargs["alt"] = "Изображение"
    elif kwargs.get("alt") and not kwargs.get("title"):
        kwargs["title"] = kwargs.get("alt")

    if kwargs.get("module"):
        del kwargs["module"]

    if kwargs.get("without_lazy"):
        img_template = "common/img_without_lazy.html"

    if not is_elist and src and "/plugs/" not in src:
        ChunkQuery.save(name=name, content=src.replace(f"/media/{get_landing().app_name}/", ""))

    content = render_to_string(
        img_template,
        {
            "media_src": src,
            "width": width,
            "height": height,
            "is_slider": is_slider,
            "is_swiper": is_swiper,
            "is_elist": is_elist,
            "attributes": kwargs,
            "module": module,
        },
        request=get_request(),
    )

    return admin_chunk_wrapper(name, content, module, is_img=True) if not is_elist else content


@register.simple_tag(takes_context=True)
def img_tag_with_preview(context, *args, **kwargs) -> str:
    """Получить тэг изображения с превью
    :param context: Контекст
    :return: str
    """
    width = kwargs.get("width")
    height = kwargs.get("height")
    class_main = kwargs.get("class_main")
    is_slider = kwargs.get("is_slider")
    template = kwargs.get("template", "img_with_preview.html")
    landing_tpl_path = get_landing_tpl_path()
    module = kwargs.get("module") if kwargs.get("module") else get_module_from_context(context)
    kwargs["module"] = module
    src = get_image_src(args, kwargs)

    if not kwargs.get("alt"):
        kwargs["alt"] = ""

    full_path = f"{settings().BASE_DIR}{src}"
    file_name, file_extension = os.path.splitext(src)
    preview_image_src = src

    if not os.path.isfile(full_path):
        if width and height:
            preview_image_src = make_img_plug(file_name, width, height, module)
        else:
            preview_image_src = make_img_plug(file_name, 100, 100, module)

    elif os.path.isfile(full_path) and not os.path.isfile(f"{settings().BASE_DIR}/{file_name}-preview{file_extension}"):

        if "/media/plugs/" in full_path:
            if width and height:
                preview_image_src = make_img_plug(file_name, width, height, module)
            else:
                preview_image_src = make_img_plug(file_name, 100, 100, module)
        else:
            # Делаем превью
            image = Image.open(full_path)
            resized_image = image.resize((width, height))
            resized_image.save(f"{settings().BASE_DIR}/{file_name}-preview{file_extension}")
            preview_image_src = f"{file_name}-preview{file_extension}"

    if os.path.isfile(settings().BASE_DIR / f"core/templates/common/modules/{module}/{landing_tpl_path}/{template}.html"):
        include_way = f"common/modules/{module}/{landing_tpl_path}/{template}.html"
    elif os.path.isfile(settings().BASE_DIR / f"core/templates/common/modules/{module}/{template}.html"):
        include_way = f"common/modules/{module}/{template}.html"
    else:
        include_way = f"common/{template}"

    content = render_to_string(
        include_way,
        {
            "full_image_src": src,
            "preview_image_src": preview_image_src,
            "width": width,
            "height": height,
            "is_slider": is_slider,
            "class_main": class_main,
            "attributes": kwargs,
        },
        request=get_request(),
    )

    return content


@register.simple_tag(takes_context=True)
def media_tag_src(context, *args, **kwargs) -> str:
    """Получить путь медиафайла
    :param context: Контекст
    :return: str
    """
    name = args[0] + ""
    module = kwargs.get("module") if kwargs.get("module") else get_module_from_context(context)
    kwargs["module"] = module
    media_root = settings().MEDIA_ROOT
    media_url = settings().MEDIA_URL
    src = None

    existing = search_existing_chunk(name)

    if existing:
        path = existing.content
    else:
        path = name

    if os.path.isfile(media_root / "common" / path):
        src = f"{media_url}common/{path}"

    elif os.path.isfile(media_root / f"{module}/common" / path):
        src = f"{media_url}{module}/common/{path}"

    elif os.path.isfile(media_root / path):
        src = f"{media_url}{path}"

    elif os.path.isfile(media_root / f"{module}/{path}"):
        src = f"{media_url}{module}/{path}"

    return src


@register.simple_tag(takes_context=True)
def media_tag(context, *args, **kwargs) -> str:
    """Получить тэг изображения
    :param context: Контекст
    :return: str
    """
    name = args[0] + ""
    landing = get_landing()
    width = kwargs.get("width")
    height = kwargs.get("height")
    is_slider = kwargs.get("is_slider")
    module = kwargs.get("module") if kwargs.get("module") else get_module_from_context(context)
    kwargs["module"] = module
    media_template = "common/media.html"
    allowed_extensions = (".mp4", ".webm")
    file_type = "video"
    src = get_image_src(args, kwargs, custom_plug="media")
    path = src.replace(f"media/{landing.app_name}/", "")[1:]
    _, file_extension = os.path.splitext(src)

    src_mp4 = (
        src.replace(name, kwargs.get("mp4")).replace(file_extension, ".mp4")
        if kwargs.get("mp4") and kwargs.get("mp4") != "false" and file_extension != ".mp4"
        else src.replace(".webm", ".mp4")
    )
    path_mp4 = (
        path.replace(name, kwargs.get("mp4")).replace(file_extension, ".mp4")
        if kwargs.get("mp4") and kwargs.get("mp4") != "false" and file_extension != ".mp4"
        else src_mp4.replace(f"media/{landing.app_name}/", "")[1:]
    )
    has_file = False
    has_file_mp4 = False
    media_root = settings().MEDIA_ROOT

    if kwargs.get("module"):
        del kwargs["module"]

    if kwargs.get("without_lazy"):
        media_template = "common/media_without_lazy.html"

    if os.path.isfile(media_root / path):
        has_file = True

    if os.path.isfile(media_root / path_mp4):
        has_file_mp4 = True

    if file_extension not in allowed_extensions:
        file_type = "image"
    elif file_extension == ".mp4":
        has_file = False

    if not src or "/media/plugs/" in src:
        file_type = "image"
        has_file_mp4 = False
        has_file = True

    content = render_to_string(
        media_template,
        {
            "media_src": src,
            "has_file": has_file,
            "has_file_mp4": has_file_mp4,
            "video_mp4": src_mp4,
            "type": file_type,
            "width": width,
            "height": height,
            "is_slider": is_slider,
            "attributes": kwargs,
            "module": module,
        },
        request=get_request(),
    )

    return content


@register.simple_tag(takes_context=True)
def chunk(context, *args, **kwargs):
    """Рендер чанка
    :param context: Контекст
    """
    name = kwargs.get("name") if kwargs.get("name") else args[0] + ""
    raw = kwargs.get("raw", False)
    wrap = kwargs.get("wrap", True)
    module = kwargs.get("module") if kwargs.get("module") else get_module_from_context(context)

    if kwargs.get("module"):
        del kwargs["module"]

    return core_chunk(name=name, variables=kwargs, raw=raw, wrap=wrap, module=module)


@register.simple_tag
def webpack(
    asset: str, extension: str, universal: bool = False, admin: bool = False, template: str = None
) -> FileNotFoundError | None | str:
    """Подключение ассетов
    :param asset: Имя ассета
    :param extension: Расширение ассета
    :param admin: Подключение для админки
    :param universal: Подключение для универсальных блоков
    :param template: Шаблон подключения
    :return: str
    """

    connection_templates = {
        "stylesheet": "<link rel='stylesheet' href='{}'/>",
        "script": "<script src='{}'></script>",
    }

    if not template:
        return FileNotFoundError("Не был указан формат подключения!")

    connection_template = connection_templates.get(template, None)

    if not connection_template:
        return FileNotFoundError("Не найден шаблон для подключения данного формата!")

    landing = get_landing()

    if admin:
        manifest_directory = settings().BASE_DIR / "core/static/admin/build"
        manifest_file = "admin.manifest.json"
    elif universal:
        manifest_directory = settings().BASE_DIR / "core/static/universal/build"
        manifest_file = "universal.manifest.json"
    else:
        manifest_directory = settings().BASE_DIR / f"_sites/{landing.app_name}/static/{landing.app_name}/build"
        manifest_file = "manifest.json"

    try:
        with open(manifest_directory / manifest_file, "r") as file:
            manifest = json.load(file)
    except FileNotFoundError:
        if manifest_file == "admin.manifest.json":
            command_hint = "yarn run prod:admin"
        elif manifest_file == "universal.manifest.json":
            command_hint = "yarn run prod:universal"
        else:
            command_hint = f"yarn run dev land={landing.app_name}"

        raise FileNotFoundError(f"Не найден файл {manifest_file}, запусти сборку yarn! [ {command_hint} ]")

    bundle_file = manifest.get(f"{asset}.{extension}")
    if not bundle_file:
        return "" if is_dev() else None

    if admin or universal:
        file = BASE_DIR / f"core/{bundle_file}"
    else:
        file = settings().BASE_DIR / f"_sites/{landing.app_name}/{bundle_file}"

    if is_dev() and not os.path.exists(file):
        url = ""

        if not re.match(r"^(http\:\/\/|https\:\/\/)", bundle_file, re.I):
            secure = env("WEBPACK_HTTPS", landing)
            server = env("WEBPACK_DOMAIN", landing)
            port = env("WEBPACK_PORT", landing)

            if secure:
                url = f"https://{server}:{port}"
            else:
                url = f"http://{server}:{port}"

        webpack_file = f"{url}{bundle_file}"
    else:
        webpack_file = bundle_file

    webpack_template = connection_template.format(webpack_file)

    return webpack_template if webpack_template else None


@register.simple_tag
def dev_class() -> str:
    """Класс dev среды"""
    return "dev" if is_dev() else ""


@register.simple_tag
def landing_data():
    """Получить данные лэндинга
    :return: mixed
    """
    return get_landing_data()


@register.simple_tag
def module(*args, **kwargs):
    """Подключаем модуль
    :return:
    """
    name = args[0] + ""

    if kwargs.get("file") is not None and kwargs.get("file") != "":
        file = kwargs.get("file", "tpl")
    else:
        file = "tpl"

    if kwargs.get("universal") is not None:
        universal = kwargs.get("universal")
    else:
        universal = False

    if kwargs.get("universal"):
        del kwargs["universal"]

    if kwargs.get("file"):
        del kwargs["file"]

    if kwargs.get("name"):
        del kwargs["name"]

    if kwargs.get("variable") and type(kwargs.get("variable")) is list:
        result = {}
        for item in kwargs.get("variable"):
            key, value = item.split("=")

            if re.match(r'^".*"$', value):
                value = ast.literal_eval(value)

            result[key] = value

        for id, variables in result.items():
            kwargs[id] = variables

        del kwargs["variable"]

    return core_module(name=name, file=file, universal=universal, variables=kwargs)


@register.simple_tag
def rus_date(date, with_year=False, nonbsp=False, short=False):
    month = date.month
    rus_month = ""

    match month:
        case 1:
            rus_month = "января"
        case 2:
            rus_month = "февраля"
        case 3:
            rus_month = "марта"
        case 4:
            rus_month = "апреля"
        case 5:
            rus_month = "мая"
        case 6:
            rus_month = "июня"
        case 7:
            rus_month = "июля"
        case 8:
            rus_month = "августа"
        case 9:
            rus_month = "сентября"
        case 10:
            rus_month = "октября"
        case 11:
            rus_month = "ноября"
        case 12:
            rus_month = "декабря"

    if with_year:
        return mark_safe(f"{date.day}&nbsp;{rus_month}&nbsp;{date.year}&nbsp;г.")
    elif nonbsp:
        return mark_safe(f"{date.day} {rus_month}")
    elif short:
        day = f"0{date.day}" if 10 > date.day else date.day
        month = f"0{date.month}" if 10 > date.month else date.month

        return mark_safe(f"{day}.{month}")
    else:
        return mark_safe(f"{date.day}&nbsp;{rus_month}")


@register.simple_tag
def offer_month(month, text_form="1"):
    """Месяц проведения акции
    :param month: Месяц, который необходимо получить
    :param text_form: Форма, в которой необходимо получить месяц
    """
    month_dict = {
        "01": {
            "1": "Январь",
            "2": "январской",
        },
        "02": {
            "1": "Февраль",
            "2": "февральской",
        },
        "03": {
            "1": "Март",
            "2": "мартовской",
        },
        "04": {
            "1": "Апрель",
            "2": "апрельской",
        },
        "05": {
            "1": "Май",
            "2": "майской",
        },
        "06": {
            "1": "Июнь",
            "2": "июньской",
        },
        "07": {
            "1": "Июль",
            "2": "июльской",
        },
        "08": {
            "1": "Август",
            "2": "августовской",
        },
        "09": {
            "1": "Сентябрь",
            "2": "сентябрьской",
        },
        "10": {
            "1": "Октябрь",
            "2": "октябрьской",
        },
        "11": {
            "1": "Ноябрь",
            "2": "ноябрьской",
        },
        "12": {
            "1": "Декабрь",
            "2": "декабрьской",
        },
    }

    offer_month = month_dict.get(month, {}).get(text_form)

    return f"{offer_month}"


@register.simple_tag
def offer_weekday(weekday):
    match weekday:
        case "monday":
            weekday_select = 0
        case "tuesday":
            weekday_select = 1
        case "wednesday":
            weekday_select = 2
        case "thursday":
            weekday_select = 3
        case "friday":
            weekday_select = 4
        case "saturday":
            weekday_select = 5
        case "sunday":
            weekday_select = 6
        case _:
            weekday_select = 0

    return weekday_select


@register.simple_tag
def offer_end_time(
    prefix=None,
    postfix=None,
    get_timestamp=False,
    get_days_left=False,
    to_end_month=False,
    to_next_month=False,
    to_weekday=None,
    to_half_month=False,
    last_week_last_day=False,
    nbsp=False,
    sun=False,
    short=False,
):
    """Время окончания акции
    :param postfix: Постфикс
    :param prefix: Префикс
    :param get_timestamp: UNIX время
    :param get_days_left: Выводит количество оставшихся дней до окончания акции
    :param to_end_month: Выводит последний день месяца
    :param to_weekday: Обновляет акцию каждую неделю, в заданный день недели
    :param to_half_month: Акция действует либо до 15 числа текущего месяца, либо до конца месяца
    :param last_week_last_day: В последнюю неделю всегда выводит последний день месяца
    :param sun: Последний день недели
    :param short: выводит акцию числом, например 1.08
    """
    global_data = get_landing_data()
    today = datetime.date.today()
    day_of_week = today.weekday()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=6, weeks=-1)
    next_month = today.replace(day=28) + datetime.timedelta(days=4)
    last_month_day = next_month - datetime.timedelta(days=next_month.day)
    count_days_end = last_month_day - today

    if day_of_week >= 4:
        friday = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=4)
    else:
        friday = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=4, weeks=-1)

    next_monday = monday + datetime.timedelta(weeks=1)
    next_friday = friday + datetime.timedelta(weeks=1)
    next_week = next_monday if 0 < day_of_week < 5 else next_friday
    next_weekday = monday + datetime.timedelta(days=offer_weekday(to_weekday), weeks=1)
    next_last_week = sunday + datetime.timedelta(weeks=1)

    if to_end_month:
        # Продление акции на последний день месяца
        finish_date = last_month_day
    elif to_next_month:
        # Продление акции на первый день месяца
        finish_date = last_month_day + datetime.timedelta(days=1)
    elif to_weekday:
        # Продление акции по дням недели
        if sun:
            finish_date = next_last_week
        else:
            finish_date = next_weekday
        # На последних 7 днях устанавливается последний день месяца
        if count_days_end.days < 7 and last_week_last_day is True:
            finish_date = last_month_day
    elif to_half_month:
        # Продление акции до 15 числа, если день меньше 15, иначе до конца месяца
        if today.day > 15:
            finish_date = last_month_day
        else:
            finish_date = datetime.date(today.year, today.month, 15)
    else:
        finish_date = next_week

    if nbsp:
        end_time = rus_date(finish_date, nonbsp=True)
    elif short:
        end_time = rus_date(finish_date, short=True)
    else:
        end_time = rus_date(finish_date)

    # Если в новый год нужно зафиксировать дату акции на 1 января
    to_january = data_get(global_data, "new_year_date_change")
    if new_year() and to_january:
        end_time = "1&nbsp;января"

    # Возвращаем просто UNIX время
    if get_timestamp:
        return int(time.mktime(finish_date.timetuple()))

    # Возвращает количество оставшихся дней до окончания акции
    if get_days_left:
        days_diff = abs((datetime.date.fromtimestamp(int(time.mktime(finish_date.timetuple()))) - today).days)

        if postfix:
            return mark_safe(f"{days_diff}&nbsp;{postfix}")

        if postfix is not False:
            return plural(days_diff, "день|дня|дней")

        return days_diff

    # Старая, привычная функция
    if prefix:
        return mark_safe(f"{prefix}&nbsp;{end_time}")

    if prefix is not False:
        return mark_safe(f"Акция&nbsp;до&nbsp;{end_time}")
    else:
        return mark_safe(f"{end_time}")


@register.simple_tag(takes_context=True)
def custom_offer(context, elist_settings=None):
    prefix = False
    postfix = None
    get_days_left = False
    to_end_month = False
    to_next_month = False
    to_weekday = None
    to_half_month = False
    last_week_last_day = False
    nbsp = False
    sun = False
    short = False

    if not elist_settings:
        try:
            landing = get_landing()
            offer_settings = EditableList(landing).get_instance("settings_offer").list.get("1")
        except Exception:
            return False
    else:
        offer_settings = elist_settings

    if offer_settings["promo_variant"] == "to_end_month":
        to_end_month = True
    elif offer_settings["promo_variant"] == "to_half_month":
        to_half_month = True
    elif offer_settings["promo_variant"] == "to_next_month":
        to_next_month = True
    elif offer_settings["promo_variant"] == "to_weekday_sun":
        to_weekday = True
        sun = True
    elif offer_settings["promo_variant"] == "to_weekday":
        if offer_settings["to_weekday_last_week_last_day"] == "true":
            last_week_last_day = True
        if offer_settings["to_weekday"] == "false":
            to_weekday = True
        else:
            to_weekday = offer_settings["to_weekday"]

    if offer_settings["format"] == "short":
        short = True
    elif offer_settings["format"] == "nbsp":
        nbsp = True
    elif offer_settings["format"] == "get_days_left":
        get_days_left = True

    if offer_settings["prefix"]:
        prefix = offer_settings["prefix"]

    if offer_settings["postfix"]:
        postfix = offer_settings["postfix"]

    return offer_end_time(
        prefix=prefix,
        postfix=postfix,
        get_days_left=get_days_left,
        to_end_month=to_end_month,
        to_next_month=to_next_month,
        to_weekday=to_weekday,
        to_half_month=to_half_month,
        last_week_last_day=last_week_last_day,
        nbsp=nbsp,
        sun=sun,
        short=short,
    )


@register.simple_tag
def get_experience(start_year, with_postfix=True, no_space=False, plus=False, custom_postfix=None):
    if not (isinstance(start_year, int) or (isinstance(start_year, str) and start_year.isdigit())):
        return ""

    start_year = int(start_year)

    if start_year <= 0 or len(str(start_year)) != 4:
        return ""

    today = datetime.datetime.today()
    start = datetime.datetime.fromisoformat(f"{start_year}-01-01")

    diff = today - start
    diff = diff.days // 365

    experience = str(diff)

    if plus:
        experience += "+"

    if with_postfix:
        if no_space:
            experience = f'{plural(diff, "год|года|лет")}'
        else:
            experience = f'&nbsp;{plural(diff, "год|года|лет")}'

    if no_space:
        experience = f'{plural(diff, "год|года|лет")}'

    if custom_postfix:
        experience = f'{plural(diff, "год|года|лет")}'
        if no_space:
            postfix = experience.replace(f"{diff}&nbsp;", "")
        else:
            postfix = experience.replace(f"{diff}", "")
        experience = f'<span class="exp">{diff}</span> <span class="postfix">{postfix} {custom_postfix}</span>'

    return mark_safe(experience)


@register.simple_tag(takes_context=True)
def media_url(context, url: str, module=None, width=None, height=None) -> str:
    """Получить ссылку на медиа
    :param context: Контекст
    :param url: URL
    :param module: Модуль
    :param width: Ширина
    :param height: Высота
    :return: str
    """
    module = module if module else get_module_from_context(context)

    if not width and not height:
        width = 883
        height = 489

    if url.startswith("http://") or url.startswith("https://"):
        return url
    else:
        return img_src(context, url, module=module, width=width, height=height)


@register.simple_tag(takes_context=True)
def get_avg_rate(context, ceil=False):
    """Средний рейтинг"""
    rates_list = chunk(context, name="rating.list", raw=True)

    rates = []
    for index, rate in enumerate(rates_list):
        rates.append(
            {
                "max": chunk(context, name=f"rating.list.{index}.max", raw=True),
                "rate": chunk(context, name=f"rating.list.{index}.rate", raw=True),
            }
        )

    i = 0
    sum = 0

    for rate in rates:
        max = rate.get("max") / 5
        rate_normal = rate.get("rate") / max
        sum += rate_normal
        i += 1

    sum = sum / i

    result = round(sum, 1)

    return math.ceil(result) if ceil else result


@register.simple_tag(takes_context=True)
def get_map_pin(context, name=None, module=None):
    """Получить урл pin'а"""

    module = module if module else get_module_from_context(context)
    pin_name = name if name else "pin.svg"

    if os.path.isfile(settings().MEDIA_ROOT / f"{module}/{pin_name}"):
        return settings().MEDIA_URL + f"{module}/{pin_name}"
    else:
        return "media/pin.svg"


@register.simple_tag
def affiliates_count(type=None, postfix=None, end_number=False, affiliates_list=False, text_content=None):
    """Подсчёт количества филиалов
    :param type: Тип
    :return: str
    :param postfix: Постфикс
    :param affiliates_list: Список клиник
    :param text_content: Названия вместо "Клиника"
    """
    global_data = get_landing_data()

    if affiliates_list:
        count = len(affiliates_list)
    else:
        if on_moderation():
            count = len(data_get(global_data, "affiliates.list.moderate"))
        else:
            count = len(data_get(global_data, "affiliates.list.regular"))

    if text_content:
        text = plural(count, f"{text_content}")
    else:
        text = plural(count, "клиника|клиники|клиник")

    end_number_text = plural(count, "-м|-х|-и", no_space=True)

    if type == "number":
        return count
    elif type == "text":
        return text.replace(f"{count}&nbsp;", "")
    else:
        if postfix:
            if end_number:
                return mark_safe(f"{end_number_text}{postfix}")

            return mark_safe(f"{count}{postfix}")

        if end_number:
            return end_number_text

        return text


@register.simple_tag(takes_context=True)
def client_ip(context):
    """Получить IP клиента"""
    return get_client_ip(context.request)


@register.simple_tag(takes_context=True)
def get_abtest_version(context) -> str:
    """Получить версию A/B тестирования"""

    from core.helpers import get_ab_test_excluded_modules

    landing = get_landing()

    landing_module = get_module_from_context(context)

    if landing_module in get_ab_test_excluded_modules():
        return "a"

    return get_version(get_request(), landing.utm_campaign, landing.ab_test)


@register.simple_tag(takes_context=True)
def view_name(context):
    """Имя текущего view"""
    return core_view_name(context.request)


@register.simple_tag()
def get_params_url():
    """Получить GET параметры url"""

    if get_request().GET:
        for k, v in get_request().GET.items():
            if str(k) == "type" or str(k) == "quiz":
                return str(v)
            return k
        return None


@register.simple_tag
def is_working_time(with_elist=False) -> str:
    """Индикатор работы клиники"""

    timezone_dict = {
        "UTC+2": "Europe/Kaliningrad",
        "UTC+3": "Europe/Moscow",
        "UTC+4": "Europe/Samara",
        "UTC+5": "Asia/Yekaterinburg",
        "UTC+6": "Asia/Omsk",
        "UTC+7": "Asia/Krasnoyarsk",
        "UTC+8": "Asia/Irkutsk",
        "UTC+9": "Asia/Yakutsk",
        "UTC+10": "Asia/Vladivostok",
        "UTC+11": "Asia/Magadan",
        "UTC+12": "Asia/Kamchatka",
    }

    landing = get_landing()
    global_data = get_landing_data(landing)
    start = (
        search_existing_chunk("working_hours.start").content
        if search_existing_chunk("working_hours.start")
        else data_get(global_data, "working_hours.start")
    )

    end = (
        search_existing_chunk("working_hours.end").content
        if search_existing_chunk("working_hours.end")
        else data_get(global_data, "working_hours.end")
    )

    timezone = (
        search_existing_chunk("working_hours.timezone").content
        if search_existing_chunk("working_hours.timezone")
        else data_get(global_data, "working_hours.timezone")
    )

    if not start or not end or not timezone:
        return ""

    if with_elist:
        e_list = EditableList(landing).get_instance("working_hours")
        work_time_new = e_list.list if e_list else None
        work_time = None
    else:
        work_time_new = None
        work_time = data_get(global_data, "working_hours.work_time")

    company_timezone = timezone_dict[timezone] if timezone in timezone_dict else "Europe/Moscow"
    timezone_value = pytz.timezone(company_timezone)

    now = datetime.datetime.now(timezone_value)

    today = datetime.datetime.today().weekday()

    if work_time_new:
        for item, value in work_time_new.items():
            if value["day"] != "false":
                day = getattr(calendar, value["day"].upper())
                day_off = value["day_off"] if "day_off" in value and value["day_off"] != "false" else None

                if today == day and day_off:
                    return ""

                if today == day:
                    start = value["start"]
                    end = value["end"]

    if work_time:
        for item, value in work_time.items():
            day = getattr(calendar, item.upper())
            day_off = value["day_off"] if "day_off" in value and value["day_off"] != "false" else None

            if today == day and day_off:
                return ""

            if today == day:
                start = value["start"]
                end = value["end"]

    if ":" in start:
        start = now.replace(hour=int(start.split(":")[0]), minute=int(start.split(":")[1]), second=0)
    else:
        start = now.replace(hour=int(start), minute=0, second=0)

    if ":" in end:
        end = now.replace(hour=int(end.split(":")[0]), minute=int(end.split(":")[1]), second=0)
    else:
        end = now.replace(hour=int(end), minute=0, second=0)

    return "active" if start <= now < end else ""


@register.simple_tag()
def get_minmax_experience(minmax: str = "min", employees=None, postfix=True) -> str | None:
    """Получить минимальный или максимальный опыт сотрудников
    :param minmax: min или max
    :param employees: Список сотрудников, число должно быть строкой
    :param postfix: Постфикс
    :return: str|None
    """

    years = []

    for employee in employees:
        experience = employees.get(employee, {}).get("experience")
        if experience:
            experience = str(experience).replace("/[^0-9]/", "")
            years.append(experience)

    if not years:
        return None

    if minmax == "min":
        result = get_experience(max(years), postfix)
    else:
        result = get_experience(min(years), postfix)

    return result


@register.simple_tag()
def get_common_experience(employees=None, postfix=True, prefix=False) -> str:
    """Получить средний опыт сотрудников
    :param employees: Список сотрудников
    :param postfix: Постфикс
    :param prefix: Префикс
    :return: str
    """

    years = []

    for employee in employees:
        experience = employees[employee]["experience"].replace("/[^0-9]/", "")
        years.append(experience)

    year_min = min(years)
    year_max = max(years)

    if year_max == year_min:
        result = "более" + get_experience(year_min, postfix)
    else:
        if prefix:
            result = "от&nbsp;" + get_experience(year_max, False) + " до" + get_experience(year_min, postfix)
        else:
            result = get_experience(year_max, False) + "&nbsp;-" + get_experience(year_min, postfix)

    return mark_safe(result)


@register.simple_tag()
def get_rating_stars(value: str, max: str = "5") -> int:
    """Получить количество закрашенных звёзд рейтинга
    :param value: Рейтинг
    :param max: Максимальное значение
    :return: str
    """

    result = float(value) / (int(max) / 100)

    return int(result)


@register.simple_tag
def get_price(price):
    "Форматирование цены, добавление пробела"
    result = format(int(price), ",").replace(",", " ").replace(".", ",")

    return mark_safe(result)


@register.simple_tag()
def get_phones(landing=None, success=True):
    """Достать телефоны'ы для лэндинга"""

    landing = landing if landing else get_landing()

    if not landing or not landing.get_phones:
        return list()

    if not success:

        if get_request().path.lstrip("/") == "success" or get_request().path.lstrip("/") == "thank":
            return None

    return landing.get_phones.splitlines()


@register.simple_tag()
def get_socials_links(landing=None):
    """Получить ссылки на socials"""

    landing = landing if landing else get_landing()
    addition_socials = landing.link_to_addition_social
    link = dict()

    if landing.link_to_vk:
        link["vk"] = landing.link_to_vk

    if landing.link_to_tg:
        link["tg"] = landing.link_to_tg

    if landing.link_to_yt:
        link["yt"] = landing.link_to_yt

    if landing.link_to_ok:
        link["ok"] = landing.link_to_ok

    if bool(addition_socials):
        for item in addition_socials.items():
            link[item[0]] = item[1]

    return link if link else None


@register.simple_tag()
def get_custom_meta(landing=None):
    """Получить кастомные мета-теги"""

    landing = landing if landing else get_landing()
    custom_meta = landing.custom_meta_tags
    tags = list()

    if bool(custom_meta):
        for name, content in custom_meta.items():
            tags.append(f"""<meta name="{name}" content="{content}">""")

    return "\n".join(tags) if tags else None


@register.simple_tag()
def get_custom_styles(landing=None):
    """Получить кастомный css"""
    landing = landing if landing else get_landing()

    if not landing or not landing.custom_css_compiled:
        return None

    return landing.custom_css_compiled


@register.simple_tag()
def get_custom_scripts(landing=None):
    """Получить кастомные скрипты"""

    landing = landing if landing else get_landing()

    if not landing or not landing.custom_scripts:
        return False

    return landing.custom_scripts


@register.simple_tag()
def get_vars_styles(landing=None):
    """Получить vars"""

    landing = landing if landing else get_landing()

    if not landing or not landing.vars_params:
        return False

    return landing.vars_params


@register.simple_tag()
def get_phones_moderation(landing=None, success=True):
    """Достать телефоны'ы модерации для лэндинга"""

    landing = landing if landing else get_landing()

    if not landing or not landing.get_phones_moderation:
        return list()

    if not success:

        if get_request().path.lstrip("/") == "success" or get_request().path.lstrip("/") == "thank":
            return None

    return landing.get_phones_moderation.splitlines()


@register.simple_tag()
def get_favicon(landing=None):
    """Получить favicon"""
    from core.settings import MEDIA_ROOT

    landing = landing if landing else get_landing()

    if not landing or not landing.favicon:

        if landing and os.path.isfile(f"{MEDIA_ROOT}/{landing.app_name}/favicon.png"):
            return f"{landing.app_name}/favicon.png"
        else:
            return "favicon.svg"

    return landing.favicon.name


@register.simple_tag(takes_context=True)
def client_phone(context):
    return get_client_phone(context.request)


@register.simple_tag(takes_context=True)
def elist(context, elist_name: str, landing=None, request=None):
    landing = landing if landing else get_landing()
    has_active_items = True
    empty_instance = None
    page_id = list_custom = None
    page = None
    user = None
    obj_through = True
    is_local_data = False

    if context:
        request = context.get("request", None)
        page = context.get("page", None)
        user = getattr(request, "user", None)

    if isinstance(page, Page):
        page_id = page.id

    if not get_elist(landing):
        add_elist_to_globals(landing, EditableList(landing))

    e_list = get_elist(landing)
    elist_json = e_list.get_json(elist_name)

    if elist_name.startswith("modules_"):
        elist_instance = e_list.get_instance(elist_name)
        if elist_instance and hasattr(elist_instance, "list"):
            elist_items = elist_instance.list
            has_active_items = bool(sum(1 for item in elist_items.values() if item.get("display") != "false"))
        else:
            has_active_items = False

    if user and not is_content_manager(user) and not has_active_items:
        empty_instance = e_list.get_instance("modules_404")

    instance = e_list.get_instance(elist_name)

    if isinstance(instance, dict):
        obj_through = instance.get("through")
        obj_list_custom = instance.get("list_custom")
        is_local_data = True
    elif instance:
        obj_through = instance.through
        obj_list_custom = instance.list_custom

    if instance and not obj_through and obj_list_custom:
        list_custom = obj_list_custom.get(str(page_id), None) if page_id else None

    if list_custom and isinstance(instance, dict):
        instance["list"] = list_custom
    elif list_custom:
        instance.list = list_custom

    if elist_json:
        return {
            "button": e_list.parse_json(elist_name, is_local_data, obj_through),
            "instance": instance if has_active_items else empty_instance,
            "json": elist_json,
        }
    else:
        return False


@register.simple_tag(takes_context=True)
def elist_render(context, landing=None):
    if not context.request.user.is_staff:
        return ""

    return mark_safe("\n".join(str(val) for key, val in GLOBAL_VARS[core_get_current_host(landing)]["elist_forms"].items()))


@register.simple_tag
def list_count(list=None, search_item="display", search_value=None) -> int:
    count = len(list)

    for i, item in list.items():

        for name_item, value_item in item.items():

            if (
                (name_item == search_item and value_item == "false")
                or (name_item == search_item and value_item is False)
                or (name_item == search_item and value_item == "")
                or (value_item == search_value and value_item is not None)
            ):
                count = count - 1

    return count


@register.simple_tag
def children_count(elist=None, search_item="parent_id", search_value=None) -> int:
    dict_filter = {}
    for i, item in elist.items():

        for name_item, value_item in item.items():

            if name_item == search_item and isinstance(value_item, list):

                for li in value_item:

                    if str(li) == str(search_value):
                        dict_filter[i] = li

            elif name_item == search_item and str(value_item) == str(search_value):
                dict_filter[i] = value_item

    return len(dict_filter)


@register.simple_tag
def working_hours_type(works_time_start: str = None, works_time_end: str = None, works_time_format=1):
    """Вид отображения рабочих часов"""

    works_time = ""

    if works_time_format == 1:
        works_time += f"с&nbsp;{works_time_start}&nbsp;до&nbsp;{works_time_end}"
    else:
        works_time += f"{works_time_start}&nbsp;-&nbsp;{works_time_end}"

    return mark_safe(works_time)


@register.simple_tag
def list_config_math(list=None, config=None, operation="sum") -> int:
    """Получить минимальный или максимальный опыт сотрудников
    :param list: elist
    :param config: Конфиг из elist, с которым будут произведены математические вычисления
    :param operation: Математические операции: sum - сложение (по умолчанию), multiplier - умножение
    :return: int
    """

    count = None

    if operation == "sum":
        count = 0
    elif operation == "multiplier":
        count = 1

    for i, item in list.items():
        for name_item, value_item in item.items():
            if name_item == config:
                if operation == "sum":
                    count = count + int(value_item)
                elif operation == "multiplier":
                    count = count * int(value_item)
    return count


@register.simple_tag
def find_modules():
    """Получить список доступных для подключения модулей на шаблоне"""
    landing = get_landing().domain
    app_name = landing.replace("-", "_")
    app_name = app_name.replace(".", "__")
    obj_modules_template = {}
    app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")

    if app_settings_template.TEMPLATE_SITE is not None:
        template = app_settings_template.TEMPLATE_SITE
    else:
        template = app_name

    id = 0

    for root, dirs, files in os.walk(BASE_DIR, topdown=True):
        for dir_name in dirs:
            if (
                dir_name == template
                and len(os.listdir(os.path.join(root, dir_name))) != 0
                and root.find("media") == -1
                and root.find("_sites") == -1
                and root.find("core") == -1
                and root.find("static") == -1
            ):

                id += 1
                module = f"{root}".replace(f"{BASE_DIR}", "").replace("/modules/", "")

                if os.path.exists(f"{root}/{template}"):
                    # Получаем список файлов и папок внутри указанной папки
                    for item in os.listdir(f"{root}/{template}"):
                        item_path = os.path.join(f"{root}/{template}", item)

                        if os.path.isfile(item_path) and "-b.html" in item:
                            files.append(item.replace(".html", ""))

                        if os.path.isdir(item_path):
                            for item_views in os.listdir(item_path):
                                if item_views.endswith(".html"):
                                    files.append(f"{item}/" + item_views.replace(".html", ""))

                obj_modules_template[id] = {"module": module, "files": files[::-1]}

    return obj_modules_template


@register.simple_tag()
def find_alt_blocks(module_name=None):
    """Получить список алтблоков в блоке"""

    print("module_name =>", module_name)

    obj_alt_blocks = "sffsfs"

    return obj_alt_blocks


@register.simple_tag()
def find_global_chunk_panel():
    """Получить глобальную чанк-панель лендинга"""

    landing = get_landing().domain
    page_template = None

    app_name = landing.replace("-", "_")
    app_name = app_name.replace(".", "__")

    app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")

    if app_settings_template.TEMPLATE_SITE is not None:
        page_template = app_settings_template.TEMPLATE_SITE
    elif "__blank__sinergium" in app_name:
        page_template = app_name

    global_chunk_panel = f"common/blocks/chunk-panel/{page_template}/chunk-panel_global.html"

    if os.path.exists(f"{BASE_DIR}/core/templates/{global_chunk_panel}"):
        return global_chunk_panel
    else:
        return None


@register.simple_tag()
def find_cookie():
    """Находит и возвращает путь к шаблону cookie файла."""
    landing = get_landing().domain
    app_name = landing.replace("-", "_").replace(".", "__")
    cookie_module = "common/blocks/m-cookie"
    default_cookie_file = f"{cookie_module}/tpl.html"

    try:
        app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")
        page_template = app_settings_template.TEMPLATE_SITE or app_name
    except (ImportError, AttributeError):
        page_template = app_name if "__blank__sinergium" in app_name else None

    paths_to_check = [
        os.path.join(BASE_DIR, "core", "templates", cookie_module, app_name, "tpl.html"),
        (os.path.join(BASE_DIR, "core", "templates", cookie_module, page_template, "tpl.html") if page_template else None),
    ]

    for path in paths_to_check:
        if path and os.path.exists(path):
            return os.path.relpath(path, os.path.join(BASE_DIR, "core", "templates"))

    return default_cookie_file


@register.simple_tag()
def get_other_value(e_list=None, id_elem=None, variable=None):
    """Получить значение элемента в elist"""
    if e_list:
        item = e_list.get(str(id_elem))
        if item:
            if variable == "wrapper" and item.get("wrapper") == "true" and item.get("wrapper_class"):
                if not new_year():
                    wrapper_class = item.get("wrapper_class").replace("new-year", "")
                else:
                    wrapper_class = item.get("wrapper_class")
                return wrapper_class
            elif variable in item:
                return str(item[variable])
    return None


@register.simple_tag()
def is_policy_tpl():
    """Проверяет наличие шаблона для Политики конфиденциальности"""
    landing = get_landing()
    app_name = get_landing().app_name if landing else None

    if app_name:
        try:
            app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")
            page_template = app_settings_template.TEMPLATE_SITE or app_name
        except (ImportError, AttributeError):
            page_template = app_name if "__blank__sinergium" in app_name else None
        app_policy_template_path = os.path.join(BASE_DIR, "modules", "m-modals", page_template, "views", "policy.html")
        return os.path.exists(app_policy_template_path)

    return False


@register.simple_tag()
def get_policy_link(text="Политика конфиденциальности", classes=None):
    """Получить ссылку на Политику конфиденциальности"""
    landing = get_landing()

    if landing:

        classes = f'class="{classes}" ' if classes else ""
        request = get_request()
        disabled_key = f"?{DISABLED_KEY}" if DISABLED_KEY in request.GET else ""

        policy_page_data = EditableList(landing).get_instance("modules_policy")

        if policy_page_data and policy_page_data.list.get("1") is not None or is_policy_file(landing):
            return mark_safe(f'<a href="/policy{disabled_key}" {classes}target="_blank">{text}</a>')

        return mark_safe(f'<a href="javascript:void(0);" {classes}data-js="popup" data-js-popup="modal-policy">{text}</a>')

    return None


@register.simple_tag()
def pages_links():
    app_name = find_files_app()
    file_cache = os.path.join(BASE_DIR, "_sites", f"{app_name}", "cache.py")
    links = {"main": pages_list()}

    def cache_types(name_cache, code):
        cache_type_match = re.search(rf"{name_cache}_types\s*=\s*\(([^)]*)\)", code)
        if cache_type_match:
            cache_type = ast.literal_eval(cache_type_match.group(1))
            cache_type = [cache_type] if isinstance(cache_type, str) else cache_type
            # Ищет переменную salt_type
            pattern = r"salt_type\s*=\s*request\.GET\.get\(\s*['\"]([^'\"]+)['\"]\s*,"
            salt_type = re.search(pattern, code).group(1)
            salt_type = "type" if not salt_type else salt_type
            # Формирует список страниц с get параметрами
            cache_links = [f"{'' if name_cache == 'index' else name_cache}?{salt_type}={item}" for item in cache_type]
            links[name_cache] = cache_links
        return

    if os.path.exists(file_cache):
        with open(file_cache, "r") as f:
            code = f.read()
            cache_types("index", code)
            cache_types("success", code)

    return links


@register.simple_tag()
def get_media_sizes(value: str) -> dict | None:
    """
    Получить ширину и длину из строки

    :param value: Строка с шириной и длиной, разделёнными двоеточием
    :return: Словарь с ключами 'width' и 'height', или None, если формат неверен
    """

    if isinstance(value, str) and ":" in value:
        width, height = map(int, value.split(":", maxsplit=1))
        return {"width": width, "height": height}

    return None


@register.simple_tag()
def file_exists_in_module(module: str, file: str) -> bool:
    """
    Проверяет наличие файла в указанном модуле по указанному пути

    :param module: Строка с названием модуля
    :param file: Строка с путём к файлу в директории модуля
    :return: bool
    """

    landing = get_landing()
    app_name = landing.app_name if landing else None

    if app_name:
        try:
            app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")
            page_template = app_settings_template.TEMPLATE_SITE or app_name
        except (ImportError, AttributeError):
            page_template = app_name if "__blank__sinergium" in app_name else None
        paths_to_check = [
            os.path.join(BASE_DIR, "modules", module, app_name, file),
            os.path.join(BASE_DIR, "modules", module, page_template, file) if page_template else None,
        ]
        for path in paths_to_check:
            if path and os.path.exists(path):
                return True
    return False


@register.simple_tag()
def get_universal_module() -> list:
    modules = []
    path = f"{BASE_DIR}/modules_universal/"
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.isfile(f"{root}/{file}") and file.endswith(".html"):
                module = root.replace(path, "")
                modules.append(module)
    return modules
