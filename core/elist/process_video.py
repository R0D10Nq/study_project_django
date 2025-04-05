from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from core.helpers import settings
from mimetypes import MimeTypes
from core.elist.helpers import mime_list
from core.elist.cleaning_file import clean_file

import os, hashlib

incs = {}
mime_list = mime_list()


def process_video(data_json, list_key, landing, elist, media_root, video, schema, file_id=None):
    file = ContentFile(video.read(), video)
    mimetype = MimeTypes().guess_type(str(file.name))
    filename, file_extension = os.path.splitext(str(video))

    if file_extension == ".webm":
        mimetype = ("video/webm", None)

    if mimetype[0] in mime_list:
        file_extension = os.path.splitext(str(video))[1]
        item_id = str(data_json.get(list_key[0], {}).get("id"))
        item_parent_id = str(data_json.get(list_key[0], {}).get("parent_id"))
        file_name = (
            schema.get("file")
            .replace("[id]", item_id)
            .replace("[parent_id]", item_parent_id)
        )

        if "[inc]" in file_name:
            incs_key = hashlib.sha1(file_name.encode("utf-8")).hexdigest()
            if not incs.get(incs_key):
                incs[incs_key] = 1
            else:
                incs[incs_key] += 1
            file_name = file_name.replace("[inc]", str(incs[incs_key]))

        saved_video = default_storage.save(
            f'{landing.app_name}/{schema.get("path")}/uploaded/{file_name}{file_extension}',
            file,
        )
        new_file_name = saved_video.replace(f"{landing.app_name}/", "")

        # Удаление старых загруженных картинок
        clean_file(file_name, file_extension, new_file_name, schema, elist, list_key, media_root, file_id)

        return new_file_name.replace(f'{schema.get("path")}/', "")
    else:
        return JsonResponse(
            {
                "success": False,
                "error": "Неподходящий формат видео. Разрешённые: .mp4",
            }
        )
