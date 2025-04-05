from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from bs4 import BeautifulSoup

from core.data import GLOBAL_VARS
from core.models import Chunk, Landing, LocalLandingData
from core.chunks.queries.chunk import ChunkQuery
from django.template.exceptions import TemplateDoesNotExist
import os


def get_chunks(landing=None):
    """Достать все чанки для текущего лэндинга"""
    from core.helpers import get_landing, get_current_host

    landing = landing if landing else get_landing()
    host_key = get_current_host(landing)

    if landing:
        return GLOBAL_VARS.get(host_key, {}).get(f"chunks_{landing.app_name}", {})

    return None


def update_chunks(updated_chunk, landing=None):
    """Обновить чанк в закэшированных чанках"""
    from core.helpers import get_landing, clear_landing_cache

    landing = landing if landing else get_landing()
    add_chunk_to_globals(landing, updated_chunk)
    clear_landing_cache()

    return updated_chunk


def admin_chunk_wrapper(name: str, chunk_content, module, is_img=False, path=None) -> str:
    """Добавляет блок редактирования к чанку
    :param name: Имя чанка
    :param chunk_content: Контент чанка
    :param module: Модуль чанка
    :param is_img: Это изображение?
    :return: str
    """

    from core.helpers import get_request, is_content_manager

    request = get_request()
    chunk_is_str = isinstance(chunk_content, str)

    if request.user and request.user.is_staff and is_content_manager(request.user):
        if isinstance(chunk_content, int) or isinstance(chunk_content, float):
            return render_to_string(
                "common/chunk.html",
                {"name": name, "chunk_content": chunk_content, "is_img": False, "module": module},
                request=request,
            )

        chunk_content = chunk_content.strip() if chunk_is_str else chunk_content

        if not chunk_content or not len(chunk_content):
            return chunk_content
        
        html = BeautifulSoup(chunk_content, features="html.parser")
        first_element = html.find()
        count = len(html.find_all(recursive=False))

        if chunk_is_str and (chunk_content[0] != "<" or count != 1):
            return render_to_string(
                "common/chunk.html",
                {"name": name, "chunk_content": chunk_content, "is_img": is_img, "module": module},
                request=request,
            )

        else:
            if not first_element:
                raise Exception(f"First element not found - chunk: {chunk_content}")

            if is_img:
                first_element["data-js-module"] = "chunk-image"  # type: ignore
            else:
                first_element["data-js-module"] = "chunk"  # type: ignore

            first_element["data-js-chunk"] = name  # type: ignore
            first_element["data-custom-open"] = name  # type: ignore
            first_element["data-js-module-name"] = module  # type: ignore

            return mark_safe(html.prettify())

    return mark_safe(chunk_content) if not path else path


def search_existing_chunk(name, default=None):
    """Поиск существующего чанка
    :param name Имя чанка
    :param default Значение по-умолчанию
    :return: mixed
    """
    chunks = get_chunks()

    if chunks.get(name):
        return chunks.get(name)

    return default if default else None


def add_chunk_to_globals(landing: Landing, chunk_instance, local_data=None):
    """Добавление чанка в GLOBAL_VARS"""
    from urllib.parse import urlparse
    from core.helpers import get_current_host, get_request, enable_local_data

    request = get_request()
    page_path = urlparse(request.META["HTTP_REFERER"]).path if "HTTP_REFERER" in request.META else None
    host = get_current_host(landing)

    if not get_chunks(landing):
        GLOBAL_VARS[host][f"chunks_{landing.app_name}"] = {}

    if enable_local_data(request, page_path):
        GLOBAL_VARS[host][f"chunks_{landing.app_name}"][chunk_instance] = local_data
    else:
        GLOBAL_VARS[host][f"chunks_{landing.app_name}"][chunk_instance.name] = chunk_instance


def chunk(*args, **kwargs):
    """Рендер чанка
    :return: mixed
    """
    from core.helpers import (
        get_landing,
        get_current_page,
        get_landing_data,
        get_request,
        is_content_manager,
        enable_local_data,
        settings,
        get_landing_tpl_path,
        data_get, prettify_html,
        is_dev
    )

    name = kwargs.get("name")
    variables = kwargs.get("variables", {})
    raw = kwargs.get("raw", False)
    wrap = kwargs.get("wrap", True)
    module = kwargs.get("module", None)
    through = kwargs.get("through", None)
    base_dir = settings().BASE_DIR
    page = get_current_page()

    if raw:
        wrap = False

    if kwargs.get("module"):
        del kwargs["module"]

    request = get_request()
    landing_tpl_path = get_landing_tpl_path()
    content = existing_content = None
    existing = search_existing_chunk(name)
    
    if enable_local_data(request, str(request.path)):
        landing = get_landing()
        user = request.user if request.user.is_authenticated else None
        local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first()
        if local_data_instance and "chunk" in local_data_instance.temp_data and name in local_data_instance.temp_data["chunk"]:
            
            local_through = local_data_instance.temp_data["chunk"][name].get("through")
            
            if page and not local_through and local_data_instance.temp_data["chunk"][name]["custom_content"].get(str(page.id)):
                content = local_data_instance.temp_data["chunk"][name]["custom_content"].get(str(page.id))
            else:
                content = local_data_instance.temp_data["chunk"][name].get("content")
        else:
            content = None

        if content:
            return admin_chunk_wrapper(name, content, module) if wrap else prettify_html(content)

    if not existing:
        global_data = get_landing_data()
        content = data_get(global_data, name)

        if raw:
            return content

        # Если чанк список или словарь
        if content and (isinstance(content, list) or isinstance(content, dict)):
            try:
                # Ищем есть ли циферка в имени и строим имя файла без неё (чтобы не плодить файлы для каждый итерации)
                name_without_context = None
                for i in name.split("."):
                    try:
                        if isinstance(int(i), int):
                            if not name_without_context:
                                name_without_context = name.replace(f"{i}.", "")
                            else:
                                name_without_context = name_without_context.replace(f"{i}.", "")
                    except Exception:
                        pass

                if name_without_context and os.path.exists(
                    base_dir / f"core/templates/common/modules/{module}/{landing_tpl_path}/{name_without_context}.html"
                ):
                    chunk_way = f"common/modules/{module}/{landing_tpl_path}/{name_without_context}.html"
                elif os.path.exists(
                    base_dir / f"core/templates/common/modules/{module}/{landing_tpl_path}/{name}.html"
                ):
                    chunk_way = f"common/modules/{module}/{landing_tpl_path}/{name}.html"
                elif os.path.exists(base_dir / f"common/modules/{module}/{name}.html"):
                    chunk_way = f"common/modules/{module}/{name}.html"
                else:
                    chunk_way = f"common/{name}.html"

                content = render_to_string(chunk_way, {"chunk_vars": variables, "chunk_data": content}, request=request)

            except TemplateDoesNotExist as e:
                if is_dev():
                    raise TemplateDoesNotExist(e)
                content = None

            existing = ChunkQuery.save(
                name=name,
                content=prettify_html(content),
            )

        # Если чанк это html
        elif content and isinstance(content, str) and content.endswith(".html"):
            try:
                if os.path.exists(base_dir / f"core/templates/common/modules/{module}/{landing_tpl_path}/{content}"):
                    chunk_way = f"common/modules/{module}/{landing_tpl_path}/{content}"
                elif os.path.exists(base_dir / f"common/modules/{module}/{content}"):
                    chunk_way = f"common/modules/{module}/{content}"
                else:
                    chunk_way = f"common/{content}"

                content = render_to_string(chunk_way, {"chunk_vars": variables}, request=request)
            except TemplateDoesNotExist as e:
                if is_dev():
                    raise TemplateDoesNotExist(e)
                content = None

        # Если чанк строка
        elif content and isinstance(content, str):
            existing = ChunkQuery.save(
                name=name,
                content=prettify_html(content),
            )

    if isinstance(existing, Chunk):
        
        if through == "false" and existing.custom_content and page and existing.custom_content.get(str(page.id), None):
            chunk_content = existing.custom_content.get(str(page.id), None)
        elif not existing.through and page and through != "true":
            chunk_content = existing.custom_content.get(str(page.id), None)
        else:
            chunk_content = existing.content
        
        existing_content = "false" if chunk_content == "" and is_content_manager(request.user) else chunk_content
            
        return admin_chunk_wrapper(name, existing_content, module) if wrap else prettify_html(existing_content)

    if not isinstance(existing, Chunk):
        existing_content = "false" if is_content_manager(request.user) else ""

    if content:
        return admin_chunk_wrapper(name, content, module) if wrap else prettify_html(content)
    elif existing_content:
        return admin_chunk_wrapper(name, existing_content, module) if wrap else prettify_html(existing_content)
    else:
        return admin_chunk_wrapper(name, "", module) if wrap else ""
