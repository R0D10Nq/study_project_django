from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from core.helpers import (
    get_landing,
    converted_image,
    is_prod,
)
from telegram.utils.bot import Telegram
from mimetypes import MimeTypes
from core.elist.helpers import mime_list
from core.elist.cleaning_file import clean_file
from core.utils.logger import Log, LogLevels

import os, hashlib

incs = {}
mime_list = mime_list()


def process_image(
    data_json,
    list_key,
    landing,
    elist,
    media_root,
    image,
    schema,
    file_id=None,
    request=None,
):
    file = ContentFile(image.read(), image)
    file_size = image.size
    mimetype = MimeTypes().guess_type(str(file.name))
    _, file_extension = os.path.splitext(str(image))

    if file_extension == ".webp":
        mimetype = ("image/webp", None)

    if mimetype[0] in mime_list:
        _, file_extension = os.path.splitext(str(image))
        item_id = str(data_json.get(list_key[0], {}).get("id"))
        item_parent_id = str(data_json.get(list_key[0], {}).get("parent_id"))
        file_name = schema.get("file").replace("[id]", item_id).replace("[parent_id]", item_parent_id)
        is_svg = file_extension == ".svg" or file_extension == ".svg+xml"

        if file_id is not None:
            file_name = file_name.replace("[inc]", str(file_id + 1))
        else:
            if "[inc]" in file_name:
                incs_key = hashlib.sha1(file_name.encode("utf-8")).hexdigest()
                if not incs.get(incs_key):
                    incs[incs_key] = 1
                else:
                    incs[incs_key] += 1
                file_name = file_name.replace("[inc]", str(incs[incs_key]))

        saved_image = default_storage.save(
            f'{landing.app_name}/{schema.get("path")}/uploaded/{file_name}{file_extension}',
            file,
        )
        new_file_name = saved_image.replace(f"{landing.app_name}/", "")

        # Сжимаем картинку при загрузке
        if is_prod() and not is_svg and file_size >= 204800:
            result = converted_image(f"{media_root}/{new_file_name}")

            if result is None or not isinstance(result, str):
                telegram_message = """*🔴 Django Landings - модуль ImageCompressed*\n--------------------------\n"""
                telegram_message += (
                    f"""*Пользователь*: *{request.user.first_name} {request.user.last_name}*\n*Лэндинг*: *{get_landing().domain}*\n"""
                )
                telegram_message += f"*Ошибка*: {result['error']}" if result["error"] else "Не удалось сжать изображение!"
                Telegram(chat_id="system").send_message(telegram_message)
                Log(telegram_message, LogLevels.ERROR)

        # Удаление старых загруженных картинок
        clean_file(file_name, file_extension, new_file_name, schema, elist, list_key, media_root, file_id)

        return new_file_name.replace(f'{schema.get("path")}/', "")
    else:
        return JsonResponse(
            {
                "success": False,
                "error": "Неподходящий формат изображения. Разрешенные: .jpg, .jpeg, .png, .webp, .svg",
            }
        )
