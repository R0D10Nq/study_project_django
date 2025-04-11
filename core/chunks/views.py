from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.html import escape

from telegram.utils.bot import Telegram
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
    get_current_page,
    enable_local_data,
)
from core.settings import BASE_DIR

import os
import re
import logging
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Union

logger = logging.getLogger('chunks')


@csrf_protect
@require_POST
def chunk_update(request):
    """Обновление чанка
    
    :param request: объект запроса Django
    :return: JsonResponse с результатом операции
    """
    try:
        # Получение и валидация данных из запроса
        chunk_name = request.POST.get("chunk_name")
        module_path = request.POST.get("module_path", "all")
        content = request.POST.get("content", "")
        update_image = request.FILES.get("update_image")
        is_image_update = request.POST.get("is_image_update") == "true"
        image_extension = request.POST.get("image_extension", "")
        through = request.POST.get("through") != "false"
        
        # Проверка валидности chunk_name
        if not chunk_name:
            return HttpResponseBadRequest("Отсутствует обязательный параметр chunk_name")

        # Получение контекста запроса
        page = get_current_page()
        page_id = page.id if page else None
        page_path = urlparse(request.META.get("HTTP_REFERER", "")).path
        landing = get_landing()
        
        if not landing:
            return HttpResponseBadRequest("Не удалось определить текущий лендинг")
        
        file_name = None
        is_create = False
        local_chunk = None
        
        # Определение типа SVG
        is_svg = image_extension in (".svg", ".svg+xml")
        
        # Логика для обновления изображений
        if is_image_update and not update_image:
            # Если это обновление изображения, но файл не предоставлен, 
            # получаем текущее содержимое чанка
            chunk_value = ChunkQuery.get_chunk(name=chunk_name)
            
            if not chunk_value:
                return HttpResponseBadRequest(f"Чанк {chunk_name} не найден")
                
            if not through and chunk_value.custom_content and chunk_value.custom_content.get(str(page_id)):
                content = chunk_value.custom_content[str(page_id)]
            else:
                content = chunk_value.content
        
        # Обработка загруженного изображения
        if update_image:
            # Проверка безопасности SVG-файлов
            if is_svg and check_raster_svg(update_image, is_svg):
                return JsonResponse({
                    "success": False,
                    "error": "Внутри загруженного SVG лежит растровое изображение! Картинка не заменена!",
                }, status=400)
            
            # Проверка размера файла
            image_size = update_image.size
            
            # Формирование имени файла
            if not chunk_name.endswith(image_extension):
                name, _ = os.path.splitext(str(chunk_name))
                file_name = f"{module_path}/uploaded/{name}{image_extension}"
            else:
                file_name = f"{module_path}/uploaded/{chunk_name}"

            # Формирование пути к файлу
            file_path = os.path.join(settings().MEDIA_ROOT, file_name)
            file_path_relative = file_path.replace(str(BASE_DIR), "")
            file_path_relative = re.sub(r'^\.*\/', '', file_path_relative).replace("media/", "")
            
            # Сохранение файла
            try:
                saved_image = default_storage.save(file_path_relative, ContentFile(update_image.read()))
                file_name = os.path.join("media", saved_image)
                file_name_new = saved_image.replace(f"{landing.app_name}/", "")
                
                # Сжатие изображения в production
                if is_prod and not is_svg and image_size >= 204800:
                    result = converted_image(os.path.join(settings().MEDIA_ROOT, file_name_new))
                    
                    if result is None or not isinstance(result, str):
                        if os.path.isfile(os.path.join(settings().MEDIA_ROOT, file_name_new)):
                            os.remove(os.path.join(settings().MEDIA_ROOT, file_name_new))
                            
                        # Логирование ошибки
                        logger.error(f"Ошибка сжатия изображения для чанка {chunk_name} на лендинге {landing.domain}")
                        Telegram(chat_id="system").send_message(
                            f"🔴 *ImageCompressed*: Не удалось сжать изображение!\n*Лэндинг*: *{landing.domain}*"
                        )
                        
                        return JsonResponse({
                            "success": False,
                            "error": "Неподходящий формат изображения. Разрешенные: .jpg, .jpeg, .png, .webp, .svg",
                        }, status=400)
                
                content = file_name_new
                chunk_value = ChunkQuery.get_chunk(name=chunk_name)
                is_create = chunk_value is None
                
            except Exception as e:
                logger.error(f"Ошибка при сохранении файла для чанка {chunk_name}: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "error": f"Ошибка при сохранении файла: {str(e)}",
                }, status=500)
        
        # Безопасная обработка контента, если это не файл
        if not update_image and isinstance(content, str):
            content = prettify_html(content)
        
        # Обновление чанка в БД с использованием транзакции
        with transaction.atomic():
            chunk = ChunkQuery.update(
                name=chunk_name,
                content=content,
                create=is_create,
                through=through
            )
        
        # Проверка локальных данных
        if enable_local_data(request, page_path):
            user = request.user if request.user.is_authenticated else None
            local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first()
            if local_data_instance and "chunk" in local_data_instance.temp_data:
                local_chunk = local_data_instance.temp_data["chunk"].get(chunk_name)

        # Формирование ответа
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
        
    except Exception as e:
        # Логирование необработанных исключений
        logger.error(f"Необработанная ошибка в chunk_update: {str(e)}")
        return JsonResponse({
            "success": False, 
            "error": "Произошла внутренняя ошибка сервера"
        }, status=500)


@require_GET
def chunk_get(request):
    """Получение чанка
    
    :param request: объект запроса Django
    :return: JsonResponse с данными чанка
    """
    try:
        # Получение и валидация параметров
        chunk_name = request.GET.get("chunk_name")
        module = request.GET.get("module")
        through = request.GET.get("through")
        is_image = request.GET.get("is_image") == "true"
        
        if not chunk_name:
            return HttpResponseBadRequest("Отсутствует обязательный параметр chunk_name")
        
        # Получение контекста запроса
        page_path = urlparse(request.META.get("HTTP_REFERER", "")).path
        landing = get_landing()
        page = get_current_page()
        
        if not landing:
            return HttpResponseBadRequest("Не удалось определить текущий лендинг")
        
        # Получение данных из БД с использованием select_related для оптимизации запросов
        chunk_obj = Chunk.objects.filter(landing=landing, name=chunk_name).first()
        
        local_through = through
        local_chunk = None
        chunk_content = None
        
        # Обработка локальных данных
        if enable_local_data(request, page_path):
            user = request.user if request.user.is_authenticated else None
            local_data_instance = LocalLandingData.objects.filter(
                causer=user, 
                landing=landing
            ).first()
            
            if local_data_instance and "chunk" in local_data_instance.temp_data:
                chunk_data = local_data_instance.temp_data["chunk"].get(chunk_name)
                
                if chunk_data:
                    local_chunk = True
                    
                    # Определение режима through
                    if through == "undefined" and "through" in chunk_data:
                        local_through = str(chunk_data.get("through")).lower()
                    
                    # Получение содержимого в зависимости от режима
                    if page and local_through == "false" and "custom_content" in chunk_data:
                        chunk_content = chunk_data["custom_content"].get(str(page.id))
                    else:
                        chunk_content = chunk_data.get("content")
        
        # Если нет локальных данных, получаем контент из БД
        if not local_chunk:
            chunk_content = core_chunk(name=chunk_name, module=module, wrap=False, through=through)
        
        # Определение статуса through
        if chunk_obj:
            if local_through is not None:
                through_status = local_through != "false"
            else:
                through_status = chunk_obj.through
        else:
            through_status = True
        
        # Формирование полного пути для изображений
        full_path = f"/media/{landing.app_name}/{chunk_content}" if is_image and chunk_content else None
        
        return JsonResponse({
            "success": bool(chunk_content),
            "chunk": chunk_content,
            "through": through_status,
            "full_path": full_path
        })
        
    except Exception as e:
        # Логирование необработанных исключений
        logger.error(f"Необработанная ошибка в chunk_get: {str(e)}")
        return JsonResponse({
            "success": False, 
            "error": "Произошла внутренняя ошибка сервера"
        }, status=500)
