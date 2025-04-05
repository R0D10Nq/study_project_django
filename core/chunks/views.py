from django.http import (
    JsonResponse,
)
from telegram.utils.bot import Telegram
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from core.chunks.queries.chunk import ChunkQuery
from core.models import Chunk, LocalLandingData

from core.chunks.helpers import chunk as core_chunk

from core.helpers import (
    get_landing,
    settings,
    prettify_html,
    converted_image,
    is_prod,
    check_raster_svg,
)
from core.settings import BASE_DIR

import os, re


def chunk_update(request):
    """Обновление чанка
    :param request: request
    :return: JsonResponse
    """
    from urllib.parse import urlparse
    from core.helpers import enable_local_data, get_current_page

    chunk_name = request.POST.get("chunk_name")
    module_path = request.POST.get("module_path", "all")
    content = request.POST.get("content")
    update_image = request.FILES.get("update_image")
    is_image_update = request.POST.get("is_image_update")
    image_extension = request.POST.get("image_extension")
    page = get_current_page()
    page_id = page.id if page else None
    through = False if request.POST.get("through") == "false" else True
    page_path = urlparse(request.META["HTTP_REFERER"]).path
    landing = get_landing()
    file_name = None
    is_create = False
    local_chunk = file_name = None
            
    is_svg = image_extension == ".svg" or image_extension == ".svg+xml"
    
    if is_image_update and not update_image:
        chunk_value = ChunkQuery.get_chunk(name=chunk_name)
        
        if not through and chunk_value.custom_content and chunk_value.custom_content[str(page_id)]:
            content = chunk_value.custom_content[str(page_id)]
        else:
            content = chunk_value.content
        
    if update_image:
        if is_svg:
            if check_raster_svg(update_image, is_svg):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Внутри загруженного SVG лежит растровое изображение! Картинка не заменена!",
                    }
                )
        image_size = request.FILES.get("update_image").size
        if not chunk_name.endswith(f"{image_extension}"):
            name, _ = os.path.splitext(str(chunk_name))
            file_name = f"{module_path}/uploaded/{name}{image_extension}"
        else:
            file_name = f"{module_path}/uploaded/{chunk_name}"

        file_path = os.path.join(settings().MEDIA_ROOT, file_name)

        file_path_relative = file_path.replace(str(BASE_DIR), "")
        file_path_relative = re.sub(r'^\.*\/', '', file_path_relative).replace("media/", "")
        
        saved_image = default_storage.save(file_path_relative, ContentFile(update_image.read()))
        file_name = os.path.join("media", saved_image)

        file_name_new = saved_image.replace(f"{landing.app_name}/", "")
        
        # Жмём картинку
        if is_prod and not is_svg and image_size >= 204800:
            result = converted_image(os.path.join(settings().MEDIA_ROOT, file_name_new))

            if result is None or not isinstance(result, str):
                Telegram(chat_id="system").send_message(
                    f"🔴 *ImageCompressed*: Не удалось сжать изображение!\n*Лэндинг*: *{get_landing().domain}*"
                )
                if os.path.isfile(os.path.join(settings().MEDIA_ROOT, file_name_new)):
                    os.remove(os.path.join(settings().MEDIA_ROOT, file_name_new))

                return JsonResponse(
                    {
                        "success": False,
                        "error": "Неподходящий формат изображения. Разрешенные: .jpg, .jpeg, .png, .webp, .svg",
                    }
                )

        content = file_name_new
        chunk_value = ChunkQuery.get_chunk(name=chunk_name)

        if chunk_value is None:
            is_create = True

    chunk = ChunkQuery.update(
        name=chunk_name,
        content=prettify_html(content),
        create=is_create,
        through=through
    )

    if enable_local_data(request, page_path):
        user = request.user if request.user.is_authenticated else None
        local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first()
        local_chunk = local_data_instance.temp_data["chunk"].get(chunk_name) if local_data_instance else None

    if not local_chunk:

        response = {
            "success": bool(chunk.pk) if chunk else False,
            "chunk": chunk.pk if chunk else None,
        }
    else:
        response = {
            "success": bool(chunk) if chunk else False,
            "chunk": chunk if chunk else None,
        }

    if update_image:
        response["new_src"] = f"/{file_name}"
    else:
        response["new_content"] = content

    return JsonResponse(response)


def chunk_get(request):
    """Получение чанка
    :param request: request
    :return: JsonResponse
    """
    from urllib.parse import urlparse
    from core.helpers import enable_local_data, get_current_page

    chunk_name = request.GET.get("chunk_name")
    module = request.GET.get("module")
    through = request.GET.get("through")
    is_image = request.GET.get("is_image")
    local_through = local_chunk = None
    page_path = urlparse(request.META["HTTP_REFERER"]).path
    landing = get_landing()
    page = get_current_page()
    
    chunk_obj = Chunk.objects.filter(landing=landing, name=chunk_name).first()
    
    if enable_local_data(request, page_path):
        user = request.user if request.user.is_authenticated else None
        local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first()
        local_chunk = local_data_instance.temp_data["chunk"].get(chunk_name) if local_data_instance else None
        
        if local_data_instance:
            local_through = str(local_data_instance.temp_data["chunk"][chunk_name].get("through")).lower() if through == "undefined" and local_data_instance.temp_data["chunk"].get(chunk_name) else through
                
            if page and local_through == "false" and local_data_instance.temp_data["chunk"].get(chunk_name) and local_data_instance.temp_data["chunk"][chunk_name]["custom_content"].get(str(page.id)):
                local_chunk = True
        
    if not local_chunk:
        chunk = core_chunk(name=chunk_name, module=module, wrap=False, through=through)
    else:
        if local_through != "false":
            chunk = local_data_instance.temp_data["chunk"][chunk_name].get("content")
        else:
            chunk = local_data_instance.temp_data["chunk"][chunk_name]["custom_content"].get(str(page.id))
    
    if chunk_obj:
        if local_through:
            through_status = False if local_through == "false" else True
        else:
            through_status = chunk_obj.through
    else:
        through_status = True

    print('through_status', through_status)

    return JsonResponse(
        {
            "success": bool(chunk),
            "chunk": chunk,
            "through": through_status,
            "full_path": f"/media/{landing.app_name}/{chunk}" if is_image else None
        }
    )
