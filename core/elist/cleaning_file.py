import os


def clean_file(file_name, file_extension, new_file_name, schema, elist, list_key, media_root, file_id):
    # * Чистим файлы в uploaded с тем же названием без хэша
    if f"{file_name}{file_extension}" != new_file_name.replace(f'{schema.get("path")}/uploaded/', ""):
        if os.path.isfile(media_root / f'{schema.get("path")}/uploaded/{file_name}{file_extension}'):
            os.remove(media_root / f'{schema.get("path")}/uploaded/{file_name}{file_extension}')

        if os.path.isfile(media_root / f'{schema.get("path")}/uploaded/{file_name}-preview{file_extension}'):
            os.remove(media_root / f'{schema.get("path")}/uploaded/{file_name}-preview{file_extension}')

    # * Ищем старый файл в elist, если нашли - удаляем
    if elist is not None and list_key[0] in elist.list and list_key[1] in elist.list[list_key[0]]:
        if os.path.isfile(
                media_root / f'{schema.get("path")}/{elist.list[list_key[0]][list_key[1]]}') and not file_id:
            elem_for_delete = elist.list[list_key[0]][list_key[1]]
            if elem_for_delete.startswith('uploaded/'):
                os.remove(media_root / f'{schema.get("path")}/{elem_for_delete}')
        elif file_id is not None and isinstance(elist.list[list_key[0]][list_key[1]], list):
            try:
                elem_for_delete = elist.list[list_key[0]][list_key[1]][file_id]
                if elem_for_delete.startswith('uploaded/') and os.path.isfile(
                        media_root / f'{schema.get("path")}/{elem_for_delete}'):
                    os.remove(media_root / f'{schema.get("path")}/{elem_for_delete}')
            except:
                pass
