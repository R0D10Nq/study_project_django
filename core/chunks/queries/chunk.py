from core.models import Chunk, ChunkHistory, Landing, LocalLandingData
from core.data import GLOBAL_VARS
import os, re


class ChunkQuery:
    @staticmethod
    def save_local_data_to(request, name, content, through, page_id):
        """Сохранение локальных данных в таблицу LocalLandingData"""
        from core.helpers import get_landing

        landing = get_landing()
        user = request.user if request.user.is_authenticated else None
        local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first()
        
        if not local_data_instance:
            local_data_instance = LocalLandingData.objects.create(
                causer=user,
                landing=landing,
                temp_data={"chunk": {name: {"content": content, "custom_content": {}, "through": through}}}
            )
        else:
            temp_data = local_data_instance.temp_data
            if "chunk" not in temp_data:
                temp_data["chunk"] = {}
                
            if name not in temp_data:
                temp_data["chunk"][name] = {}
                
            if through:
                temp_data["chunk"][name]["content"] = content
            else:
                temp_data["chunk"][name]["custom_content"] = {f"{str(page_id)}": content}
                
            temp_data["chunk"][name]["through"] = through
                
            local_data_instance.temp_data = temp_data
            local_data_instance.save()

        return local_data_instance

    @staticmethod
    def save(name: str, content: str):
        """Сохранение чанка
        :param name: Имя чанка
        :param content: Контент чанка
        :return: Chunk
        """
        from core.helpers import (
            prettify_html,
            get_landing,
            is_dev,
            settings,
            images_is_different,
            get_current_host,
            get_request,
        )
        from core.chunks.helpers import add_chunk_to_globals, get_chunks
        from urllib.parse import urlparse
        from core.helpers import enable_local_data

        landing = get_landing()
        request = get_request()
        page_path = urlparse(request.META["HTTP_REFERER"]).path if "HTTP_REFERER" in request.META else None
        if enable_local_data(request, page_path):
            user = request.user if request.user.is_authenticated else None
            local_data_instance = LocalLandingData.objects.filter(causer=user, landing=landing).first() if user else None

            if local_data_instance and "chunk" in local_data_instance.temp_data:
                local_chunk = local_data_instance.temp_data["chunk"].get(name)

        if is_dev():
            if not int(os.environ.get("SAVE_CHUNKS", default=0)) and not GLOBAL_VARS[get_current_host(landing)].get(
                "test_save_chunks"
            ):
                return None

        host = get_current_host(landing=landing, raw=True)
        # Проверяем, есть ли тег <chunk> в content, то удаляем данный тег
        if '<chunk' in content:
            content = re.sub(r'<chunk[^>]*>(.*?)</chunk>', r'\1', content, flags=re.DOTALL)
        content = prettify_html(content)
        settings = settings(landing)
        cached_chunks = get_chunks(landing)

        existing = None

        if len(cached_chunks) and not enable_local_data(request, page_path):
            existing = cached_chunks.get(name) if cached_chunks.get(name) else None

        if not existing:
            existing = Chunk.objects.filter(name=name, landing=landing).first()

        if existing and host and (host.endswith(".tmp.sinergium.ru") or host.endswith(".blank.sinergium.ru")):
            add_chunk_to_globals(landing=landing, chunk_instance=existing)

            return existing

        if existing and existing.content != content:
            split_new = content.split("/")
            split_original = existing.content.split("/")

            if split_new[0] == split_original[0] and split_original[1] == "uploaded":
                add_chunk_to_globals(landing=landing, chunk_instance=existing)

                return existing

            if content.endswith((".jpg", ".jpeg", ".png", ".svg", ".webp")):

                if not images_is_different(
                    f"{settings.MEDIA_ROOT}/{existing.content}",
                    f"{settings.MEDIA_ROOT}/{content}",
                ):
                    raise Exception(
                        f"Уже существует другое изображение с именем «{name}» в другом модуле\n{content}\nvs\n{existing.content}!!!"
                    )
                else:
                    add_chunk_to_globals(landing=landing, chunk_instance=existing)

                    return existing
            else:
                raise Exception(
                    f"Уже существует чанк с именем «{name}» с другим контентом\n{content}\nvs\n{existing.content}!!!"
                )

        elif existing and existing.content == content:
            add_chunk_to_globals(landing=landing, chunk_instance=existing)

            return existing

        try:
            chunk_instance = Chunk.objects.create(
                name=name,
                content=content,
                landing=landing,
            )
        except Exception as e:
            raise Exception(f"Ошибка сохранения чанка «{name}» для лэндинга «{landing}»!!! Ошибка: {str(e)}")

        if chunk_instance.id:
            # Добавляем историю создания чанка
            history = ChunkHistory.objects.create(chunk=chunk_instance, content=content)

            if not history.id and is_dev():
                raise Exception(f"Не смог сохранить историю чанка «{name}»")
        else:
            if is_dev():
                raise Exception(f"Не нашёл ни одного инстанса чанка «{name}» для сохранения или обновления")

        if enable_local_data(request, page_path) and local_chunk:
            chunk_instance = content
            add_chunk_to_globals(landing=landing, chunk_instance=name)
        else:
            add_chunk_to_globals(landing=landing, chunk_instance=chunk_instance)

        return chunk_instance

    @staticmethod
    def update(name: str, content: str, create=False, through=True):
        """Сохранение чанка
        :param name: Имя чанка
        :param content: Контент чанка
        :param create: Создать запись в бд
        :param through: Какой вид блока сквозной\не сквозной
        :return: Chunk
        """
        from core.chunks.helpers import add_chunk_to_globals, update_chunks
        from core.helpers import prettify_html, get_landing, get_current_page, is_dev, get_request, enable_local_data, clear_landing_cache
        from urllib.parse import urlparse

        request = get_request()
        landing = get_landing()
        page = get_current_page()
        page_id = page.id if page else None
        history = None

        page_path = urlparse(request.META["HTTP_REFERER"]).path

        # Сохранение локальных чанков
        if enable_local_data(request, page_path):
            chunk_instance = ChunkQuery.save_local_data_to(request, name, prettify_html(content), through, page_id)
            if chunk_instance:
                add_chunk_to_globals(landing, name, local_data=chunk_instance.temp_data["chunk"][name].get(name))
                clear_landing_cache()
                return chunk_instance.temp_data["chunk"].get(name)

        # Логика работы с базой данных
        if create:
            chunk_instance = Chunk.objects.create(
                name=name,
                content=prettify_html(content),
                landing=landing,
                through=through
            )
        else:
            chunk_instance = Chunk.objects.filter(
                name=name,
                landing=landing,
            ).first()

        if chunk_instance:
            if not through:
                if not chunk_instance.custom_content or not chunk_instance.custom_content[str(page_id)]:
                    chunk_instance.custom_content = {}
                    chunk_instance.custom_content[str(page_id)] = prettify_html(content)
                    chunk_instance.through = through
                    chunk_instance.save()
                elif chunk_instance.custom_content and chunk_instance.custom_content[str(page_id)] and page_id:
                    # Если он есть и контент различается — обновляем
                    if chunk_instance.custom_content[str(page_id)] != prettify_html(content):
                        chunk_instance.custom_content[str(page_id)] = prettify_html(content)
                        chunk_instance.through = through
                        chunk_instance.save()

                        # Добавляем историю изменения чанка
                        history = ChunkHistory.objects.create(
                            chunk=chunk_instance,
                            custom_content=prettify_html(content),
                        )

                        update_chunks(chunk_instance, landing)
                        
                    elif chunk_instance.through != through:
                        chunk_instance.through = through
                        chunk_instance.save()
            else:
                # Если он есть и контент различается — обновляем
                if chunk_instance.content != prettify_html(content):
                    chunk_instance.content = prettify_html(content)
                    chunk_instance.through = through
                    chunk_instance.save()

                    # Добавляем историю изменения чанка
                    history = ChunkHistory.objects.create(
                        chunk=chunk_instance,
                        content=prettify_html(content),
                    )

                    update_chunks(chunk_instance, landing)
                    
                elif chunk_instance.through != through:
                    chunk_instance.through = through
                    chunk_instance.save()
                    
            if history and not history.id and is_dev():
                raise Exception(f"Не смог сохранить историю чанка «{name}»")
        else:
            if is_dev():
                raise Exception(f"Не нашёл ни одного инстанса чанка «{name}» для сохранения или обновления")

        return chunk_instance

    @staticmethod
    def get_chunk(name):
        """Получить чанк
        :param name: Имя чанка
        :return: Chunk
        """
        from core.helpers import get_landing

        return Chunk.objects.filter(
            name=name,
            landing=get_landing(),
        ).first()

    @staticmethod
    def share_chunks(landing: Landing = None):
        """Шарит глобально все чанки
        :return: list
        """
        from core.chunks.helpers import add_chunk_to_globals
        from core.helpers import get_landing, get_current_host

        landing = get_landing() if not landing else landing
        host_key = get_current_host(landing)

        if type(landing) is Landing:
            if not GLOBAL_VARS.get(host_key):
                GLOBAL_VARS[host_key] = {}

            for chunk in Chunk.objects.filter(landing=landing).all():
                add_chunk_to_globals(landing, chunk)
