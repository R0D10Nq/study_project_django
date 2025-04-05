from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from mergedeep import merge
from core.elist.helpers import alt_blocks_check
from core.helpers import get_landing, settings, check_raster_svg, get_template
from core.models import EList, LocalLandingData
from core.elist.process_image import process_image
from core.elist.process_video import process_video
from core.utils.elist import EditableList
import os, re, json


@csrf_exempt
def elist(request):
    """Сохранить редактируемый список"""
    from core.helpers import clear_landing_cache, enable_local_data, get_current_page
    from urllib.parse import urlparse

    landing = get_landing()
    page = get_current_page()
    page_id = page.id if page else None
    elist_name = request.POST.get("elist_name")
    elist_through = False if request.POST.get("through") == "false" else True
    json_name = (
        "modules_proto"
        if elist_name == "modules_proto"
        else "modules" if ("modules_" in elist_name and elist_name is not None) else elist_name
    )
    page_path = urlparse(request.META["HTTP_REFERER"]).path
    local_data_status = enable_local_data(request, page_path)

    elist_obj = EList.objects.filter(landing=landing, name=elist_name).first()

    if local_data_status:
        user = request.user if request.user.is_authenticated else None

        local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first()

        if not local_data_instance:
            local_data_instance = LocalLandingData.objects.create(causer=user, landing=landing, temp_data={})

        temp_data = local_data_instance.temp_data

        local_data = local_data_instance.temp_data or {}
        local_through = local_data["elist"][elist_name].get("through")

        if local_data and elist_through and not local_through:
            local_data["elist"][elist_name]["through"] = elist_through
            local_data_instance.save()
            return JsonResponse({"success": True})

        local_elist_custom = (
            local_data["elist"][elist_name].get("list_custom").get(str(page_id))
            if local_data and local_data["elist"][elist_name].get("list_custom")
            else None
        )

        if local_data and not elist_through and elist_obj.through and local_elist_custom:
            local_data["elist"][elist_name]["through"] = elist_through
            local_data_instance.save()
            return JsonResponse({"success": True})

        if "elist" not in temp_data:
            temp_data["elist"] = {}

        if elist_name not in temp_data:
            temp_data["elist"][elist_name] = {}

        temp_data["elist"][elist_name]["through"] = elist_through

    # Выходим из цикла если переключили на сквозной блок
    if elist_obj and elist_through and not elist_obj.through:
        elist_obj.through = elist_through
        elist_obj.save()
        return JsonResponse({"success": True})

    elist_custom = elist_obj.list_custom.get(str(page_id)) if elist_obj and elist_obj.list_custom else None

    # Выходим из цикла если переключили на не сквозной блок
    if elist_obj and not elist_through and elist_obj.through and elist_custom:
        elist_obj.through = elist_through
        elist_obj.save()
        return JsonResponse({"success": True})

    base_dir = settings(landing).BASE_DIR
    media_root = settings(landing).MEDIA_ROOT

    json_dir = base_dir / f"_sites/{landing.app_name}/elists/{json_name}.json"

    if os.path.exists(json_dir):
        json_dir = json_dir
    elif os.path.exists(base_dir / f"core/templates/json/{json_name}.json"):
        json_dir = base_dir / f"core/templates/json/{json_name}.json"
    else:
        app_template = get_template(landing.app_name) if get_template(landing.app_name) else landing.app_name
        if base_dir / f"_sites/{app_template}/elists/{json_name}.json":
            json_dir = base_dir / f"_sites/{app_template}/elists/{json_name}.json"

    if os.path.exists(json_dir):
        with open(json_dir, "r") as jf:
            e_list = json.load(jf)
    else:
        return JsonResponse({"success": False, "error": "Такого конфига не существует"})

    data_json = {}
    name_list = id_list = None

    # * Обработка текста и списка изображений
    for k, v in request.POST.items():
        list_key = re.findall(r"\[([^\[\]]+)\]", k)

        if len(list_key) < 2:
            continue

        if not (data_json.get(list_key[0])):
            data_json[list_key[0]] = {}

        schema = e_list.get("fields").get(list_key[1])

        if list_key[1] == "id":
            data_json[list_key[0]][list_key[1]] = int(v)
        elif schema and (schema.get("type") == "img-list" or schema.get("type") == "text-list"):

            if list_key[0] != id_list or list_key[1] != name_list:
                data_json[list_key[0]][list_key[1]] = []

                if v == "false" or v == "":
                    data_json[list_key[0]][list_key[1]] = False
                else:
                    data_json[list_key[0]][list_key[1]].append(v)
            elif v != "":
                data_json[list_key[0]][list_key[1]].append(v)

            name_list = list_key[1]
            id_list = list_key[0]

        else:
            data_json[list_key[0]][list_key[1]] = v

    # Добавление alt_blocks в конфиг, для новых добавленных блоков
    for k, v in request.POST.items():
        list_key = re.findall(r"\[([^\[\]]+)\]", k)

        if len(list_key) > 1 and list_key[1] == "module":
            alt_blocks_value = request.POST.get(f"elist[{list_key[0]}][alt_blocks]")
            if not alt_blocks_value or alt_blocks_value == "false":
                file_value = request.POST.get(f"elist[{list_key[0]}][file]")
                file_value = file_value if file_value else None
                alt_blocks = alt_blocks_check(v, file_value)
                if alt_blocks:
                    data_json[list_key[0]]["alt_blocks"] = alt_blocks

    # * Обработка картинок
    for k, v in request.FILES.items():
        list_key = re.findall(r"\[([^\[\]]+)\]", k)
        if len(list_key) < 2:
            continue

        if not (data_json.get(list_key[0])):
            data_json[list_key[0]] = {}

        schema = e_list.get("fields").get(list_key[1])

        if not elist_through and page_id:
            schema["file"] = f"{schema.get('file')}_{page_id}"

        match schema.get("type"):
            case "img":
                if not check_raster_svg(v):
                    data_json[list_key[0]][list_key[1]] = process_image(
                        data_json, list_key, landing, elist_obj, media_root, v, schema, request=request
                    )
                else:
                    return JsonResponse({"success": False, "error": f"Внутри {str(v)} лежит растровое изображение! Картинка не заменена!"})

            case "video":
                data_json[list_key[0]][list_key[1]] = process_video(data_json, list_key, landing, elist_obj, media_root, v, schema)

            case "media":
                _, file_extension = os.path.splitext(str(v))
                video_extension = [".mp4", ".webm"]

                if file_extension in video_extension:
                    data_json[list_key[0]][list_key[1]] = process_video(data_json, list_key, landing, elist_obj, media_root, v, schema)
                else:
                    if not check_raster_svg(v):
                        data_json[list_key[0]][list_key[1]] = process_image(
                            data_json, list_key, landing, elist_obj, media_root, v, schema, request=request
                        )
                    else:
                        return JsonResponse(
                            {"success": False, "error": f"Внутри {str(v)} лежит растровое изображение! Картинка не заменена!"}
                        )

            case "img-list":
                if not (data_json.get(list_key[0], {}).get(list_key[1])):
                    data_json[list_key[0]][list_key[1]] = []

                if not check_raster_svg(v):
                    index_file = int(k.split("[")[3][0])
                    data_json[list_key[0]][list_key[1]].insert(
                        index_file,
                        process_image(data_json, list_key, landing, elist_obj, media_root, v, schema, index_file, request=request),
                    )
                else:
                    return JsonResponse({"success": False, "error": f"Внутри {str(v)} лежит растровое изображение! Картинка не заменена!"})

            case "media-list":
                _, file_extension = os.path.splitext(str(v))
                video_extension = [".mp4", ".webm"]

                if not (data_json.get(list_key[0], {}).get(list_key[1])):
                    data_json[list_key[0]][list_key[1]] = []

                index_file = int(k.split("[")[3][0])

                if file_extension in video_extension:
                    data_json[list_key[0]][list_key[1]].append(
                        process_video(data_json, list_key, landing, elist_obj, media_root, v, schema, index_file)
                    )
                else:
                    if not check_raster_svg(v):
                        data_json[list_key[0]][list_key[1]].append(
                            process_image(data_json, list_key, landing, elist_obj, media_root, v, schema, index_file, request=request)
                        )
                    else:
                        return JsonResponse(
                            {"success": False, "error": f"Внутри {str(v)} лежит растровое изображение! Картинка не заменена!"}
                        )

            case _:
                raise Exception("Неизвестный формат поля!")

    def find_by_id(obj, obj_id):
        if "id" in obj:
            return obj.get("id")

        for _, item_value in obj.items():
            if isinstance(item_value, dict):
                elem = find_by_id(item_value, obj_id)
                if elem == obj_id:
                    return item_value

    if elist_obj:
        tmp_data = {}

        for order, item in data_json.items():

            if not elist_through and elist_custom:
                db_item = find_by_id(elist_custom, item.get("id"))
            else:
                db_item = find_by_id(elist_obj.list, item.get("id"))

            if db_item is not None:
                # * Очистка списков
                for r_key, r_fields in item.items():
                    if r_fields is list:
                        del db_item[r_key]

                tmp_data[order] = merge(db_item, item)
            else:
                tmp_data[order] = item

        data_json = tmp_data

        if local_data_status:

            if elist_through:
                temp_data["elist"][elist_name]["list"] = data_json
            else:
                temp_data["elist"][elist_name]["list_custom"] = {f"{str(page_id)}": data_json}

            local_data_instance.temp_data = temp_data
            local_data_instance.save()
        else:
            if elist_through:
                elist_obj.list = data_json

            elist_obj.through = elist_through
            elist_obj.save()

    else:

        for item_id, item in data_json.items():
            exists = list(map(lambda x: x, item))

            for f, _ in e_list.get("fields").items():
                if f not in exists:
                    data_json[item_id][f] = None

        if local_data_status:
            if elist_through:
                temp_data["elist"][elist_name]["list"] = data_json
            else:
                temp_data["elist"][elist_name]["list_custom"] = {f"{str(page_id)}": data_json}

            local_data_instance.temp_data = temp_data
            local_data_instance.save()

        else:
            elist_obj = EList.objects.create(landing=landing, name=elist_name, list=data_json, through=elist_through)

    custom_data = {}

    if not local_data_status and not elist_through and page_id:

        if not elist_obj.list_custom:
            custom_data[page_id] = data_json
            elist_obj.list_custom = custom_data
            elist_obj.save()
        else:
            elist_obj.list_custom[page_id] = data_json
            elist_obj.save()

    EditableList(landing).prepare_json(elist_name, elist_obj)

    return JsonResponse(
        {
            "success": True,
            "data_json": data_json,
            "clear_cache": clear_landing_cache(landing),
        }
    )
