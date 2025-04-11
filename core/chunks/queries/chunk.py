from core.models import Chunk, ChunkHistory, Landing, LocalLandingData
from core.data import GLOBAL_VARS
from django.db import transaction
from django.core.cache import cache
from django.utils.html import escape
from django.db.models import Q

import os
import re
import logging
from typing import Optional, Dict, Any, Union, List

logger = logging.getLogger('chunks')


class ChunkQuery:
    """Класс для работы с чанками в базе данных
    
    Предоставляет методы для создания, обновления и получения
    чанков, а также для работы с локальными данными.
    """
    
    @staticmethod
    def save_local_data_to(request, name: str, content: str, through: bool, page_id: Optional[int]) -> Optional[LocalLandingData]:
        """Сохранение локальных данных в таблицу LocalLandingData
        
        :param request: Объект запроса Django
        :param name: Имя чанка
        :param content: Контент чанка
        :param through: Флаг "сквозного" чанка
        :param page_id: ID страницы
        :return: Экземпляр LocalLandingData или None в случае ошибки
        """
        try:
            from core.helpers import get_landing
            
            if not request or not name:
                logger.warning("Невозможно сохранить локальные данные: отсутствуют обязательные параметры")
                return None
                
            landing = get_landing()
            if not landing:
                logger.warning("Невозможно сохранить локальные данные: не удалось получить лендинг")
                return None
                
            user = request.user if request.user.is_authenticated else None
            
            # Используем select_related для оптимизации запроса
            local_data_instance = LocalLandingData.objects.filter(
                causer=user, 
                landing=landing
            ).first()
            
            # Если записи нет, создаем новую
            if not local_data_instance:
                local_data_instance = LocalLandingData.objects.create(
                    causer=user,
                    landing=landing,
                    temp_data={"chunk": {name: {"content": content, "custom_content": {}, "through": through}}}
                )
            else:
                # Обновляем существующую запись
                temp_data = local_data_instance.temp_data
                
                if "chunk" not in temp_data:
                    temp_data["chunk"] = {}
                    
                if name not in temp_data["chunk"]:
                    temp_data["chunk"][name] = {}
                    
                # Сохраняем контент в зависимости от типа чанка
                if through:
                    temp_data["chunk"][name]["content"] = content
                else:
                    if "custom_content" not in temp_data["chunk"][name]:
                        temp_data["chunk"][name]["custom_content"] = {}
                    
                    temp_data["chunk"][name]["custom_content"][str(page_id)] = content
                    
                temp_data["chunk"][name]["through"] = through
                
                # Атомарно обновляем запись в БД
                with transaction.atomic():
                    local_data_instance.temp_data = temp_data
                    local_data_instance.save()

            return local_data_instance
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении локальных данных для чанка {name}: {str(e)}")
            return None

    @staticmethod
    def save(name: str, content: str) -> Optional[Chunk]:
        """Сохранение чанка
        
        :param name: Имя чанка
        :param content: Контент чанка
        :return: Экземпляр Chunk или None в случае ошибки
        """
        try:
            from core.helpers import (
                prettify_html,
                get_landing,
                is_dev,
                settings,
                images_is_different,
                get_current_host,
                get_request,
                enable_local_data,
            )
            from core.chunks.helpers import add_chunk_to_globals, get_chunks
            from urllib.parse import urlparse
            
            # Валидация входных данных
            if not name:
                logger.warning("Невозможно сохранить чанк: отсутствует имя чанка")
                return None
                
            # Получение контекста
            landing = get_landing()
            if not landing:
                logger.warning("Невозможно сохранить чанк: не удалось получить лендинг")
                return None
                
            request = get_request()
            page_path = urlparse(request.META.get("HTTP_REFERER", "")).path if request and "HTTP_REFERER" in request.META else None
            
            # Проверка локальных данных
            local_chunk = None
            if page_path and enable_local_data(request, page_path):
                user = request.user if request.user.is_authenticated else None
                local_data_instance = LocalLandingData.objects.filter(
                    causer=user, 
                    landing=landing
                ).first() if user else None

                if local_data_instance and "chunk" in local_data_instance.temp_data:
                    local_chunk = local_data_instance.temp_data["chunk"].get(name)

            # В режиме разработки проверяем настройки сохранения чанков
            if is_dev():
                if not int(os.environ.get("SAVE_CHUNKS", default=0)) and not GLOBAL_VARS.get(
                    get_current_host(landing), {}
                ).get("test_save_chunks"):
                    return None

            # Подготовка данных для сохранения
            host = get_current_host(landing=landing, raw=True)
            
            # Удаление тегов <chunk> из контента для безопасности
            if '<chunk' in content:
                content = re.sub(r'<chunk[^>]*>(.*?)</chunk>', r'\1', content, flags=re.DOTALL)
                
            content = prettify_html(content)
            app_settings = settings(landing)
            
            # Проверка кэша
            cache_key = f"chunk_{landing.id}_{name}"
            existing = cache.get(cache_key)
            
            # Если нет в кэше, получаем из закэшированных чанков
            if not existing:
                cached_chunks = get_chunks(landing)
                if len(cached_chunks) and not (page_path and enable_local_data(request, page_path)):
                    existing = cached_chunks.get(name)

            # Если все еще нет, запрашиваем из БД
            if not existing:
                existing = Chunk.objects.filter(name=name, landing=landing).first()

            # Обработка особых случаев для временных доменов
            if existing and host and (host.endswith(".tmp.sinergium.ru") or host.endswith(".blank.sinergium.ru")):
                add_chunk_to_globals(landing=landing, chunk_instance=existing)
                return existing

            # Обработка случая, когда путь к загруженному файлу
            if existing and existing.content != content:
                split_new = content.split("/")
                split_original = existing.content.split("/")

                if split_new and split_original and len(split_new) > 1 and len(split_original) > 1:
                    if split_new[0] == split_original[0] and split_original[1] == "uploaded":
                        add_chunk_to_globals(landing=landing, chunk_instance=existing)
                        return existing

                # Проверка изображений
                if content.endswith((".jpg", ".jpeg", ".png", ".svg", ".webp")):
                    if not images_is_different(
                        f"{app_settings.MEDIA_ROOT}/{existing.content}",
                        f"{app_settings.MEDIA_ROOT}/{content}",
                    ):
                        logger.warning(
                            f"Уже существует другое изображение с именем «{name}» в другом модуле: {content} vs {existing.content}"
                        )
                        add_chunk_to_globals(landing=landing, chunk_instance=existing)
                        return existing
                    else:
                        logger.warning(
                            f"Уже существует чанк с именем «{name}» с другим контентом: {content} vs {existing.content}"
                        )
                        add_chunk_to_globals(landing=landing, chunk_instance=existing)
                        return existing
                else:
                    logger.warning(
                        f"Уже существует чанк с именем «{name}» с другим контентом: {content} vs {existing.content}"
                    )
                    add_chunk_to_globals(landing=landing, chunk_instance=existing)
                    return existing

            # Если контент совпадает, просто возвращаем существующий чанк
            elif existing and existing.content == content:
                add_chunk_to_globals(landing=landing, chunk_instance=existing)
                return existing

            # Создание нового чанка с использованием транзакции
            try:
                with transaction.atomic():
                    chunk_instance = Chunk.objects.create(
                        name=name,
                        content=content,
                        landing=landing,
                    )
                    
                    # Создание записи в истории
                    history = ChunkHistory.objects.create(chunk=chunk_instance, content=content)
                    
                    # Кэширование результата
                    cache.set(cache_key, chunk_instance, 3600)  # Кэшируем на час
            except Exception as e:
                logger.error(f"Ошибка сохранения чанка «{name}» для лэндинга «{landing}»: {str(e)}")
                return None

            # Проверка успешного создания
            if not chunk_instance.id:
                if is_dev():
                    logger.error(f"Не нашёл ни одного инстанса чанка «{name}» для сохранения или обновления")
                return None

            # Обработка локальных данных
            if page_path and enable_local_data(request, page_path) and local_chunk:
                add_chunk_to_globals(landing=landing, chunk_instance=name)
            else:
                add_chunk_to_globals(landing=landing, chunk_instance=chunk_instance)

            return chunk_instance
            
        except Exception as e:
            logger.error(f"Необработанная ошибка при сохранении чанка {name}: {str(e)}")
            return None

    @staticmethod
    def update(name: str, content: str, create: bool = False, through: bool = True) -> Optional[Chunk]:
        """Обновление чанка
        
        :param name: Имя чанка
        :param content: Контент чанка
        :param create: Создать запись в бд, если чанк не существует
        :param through: Флаг "сквозного" чанка (общего для всех страниц)
        :return: Экземпляр Chunk или None в случае ошибки
        """
        try:
            from core.chunks.helpers import add_chunk_to_globals, update_chunks
            from core.helpers import (
                prettify_html, 
                get_landing, 
                get_current_page, 
                is_dev, 
                get_request, 
                enable_local_data, 
                clear_landing_cache
            )
            from urllib.parse import urlparse
            
            # Валидация входных данных
            if not name:
                logger.warning("Невозможно обновить чанк: отсутствует имя чанка")
                return None
                
            # Получение контекста
            request = get_request()
            landing = get_landing()
            if not landing:
                logger.warning("Невозможно обновить чанк: не удалось получить лендинг")
                return None
                
            page = get_current_page()
            page_id = page.id if page else None
            page_path = urlparse(request.META.get("HTTP_REFERER", "")).path if "HTTP_REFERER" in request.META else None
            
            # Подготовка контента
            safe_content = prettify_html(content)
            history = None

            # Сохранение локальных чанков
            if page_path and enable_local_data(request, page_path):
                chunk_instance = ChunkQuery.save_local_data_to(request, name, safe_content, through, page_id)
                if chunk_instance and "chunk" in chunk_instance.temp_data and name in chunk_instance.temp_data["chunk"]:
                    # Обновление глобальных данных и кэша
                    add_chunk_to_globals(landing, name, local_data=chunk_instance.temp_data["chunk"].get(name))
                    clear_landing_cache()
                    
                    # Инвалидация кэша для этого чанка
                    cache_key = f"chunk_{landing.id}_{name}"
                    cache.delete(cache_key)
                    
                    return chunk_instance.temp_data["chunk"].get(name)

            # Логика работы с базой данных в транзакции
            with transaction.atomic():
                # Создание нового чанка, если нужно
                if create:
                    chunk_instance = Chunk.objects.create(
                        name=name,
                        content=safe_content,
                        landing=landing,
                        through=through
                    )
                    
                    # Создание записи в истории
                    history = ChunkHistory.objects.create(chunk=chunk_instance, content=safe_content)
                else:
                    # Получение существующего чанка
                    chunk_instance = Chunk.objects.filter(
                        name=name,
                        landing=landing,
                    ).first()

                # Обновление существующего чанка
                if chunk_instance:
                    modified = False
                    
                    # Обработка не-сквозных чанков (специфичных для страницы)
                    if not through:
                        # Инициализация custom_content, если нужно
                        if not chunk_instance.custom_content:
                            chunk_instance.custom_content = {}
                        
                        # Обновление контента для конкретной страницы
                        if page_id and (
                            not chunk_instance.custom_content.get(str(page_id)) or 
                            chunk_instance.custom_content.get(str(page_id)) != safe_content
                        ):
                            chunk_instance.custom_content[str(page_id)] = safe_content
                            modified = True
                            
                        # Обновление флага through, если нужно
                        if chunk_instance.through != through:
                            chunk_instance.through = through
                            modified = True
                    else:
                        # Обновление для сквозных чанков
                        if chunk_instance.content != safe_content:
                            chunk_instance.content = safe_content
                            modified = True
                        
                        # Обновление флага through, если нужно
                        if chunk_instance.through != through:
                            chunk_instance.through = through
                            modified = True
                    
                    # Сохраняем изменения, только если что-то изменилось
                    if modified:
                        chunk_instance.save()
                        
                        # Создание записи в истории
                        if not through and page_id:
                            history = ChunkHistory.objects.create(
                                chunk=chunk_instance,
                                custom_content=safe_content,
                            )
                        else:
                            history = ChunkHistory.objects.create(
                                chunk=chunk_instance,
                                content=safe_content,
                            )
                        
                        # Обновление кэша и глобальных данных
                        update_chunks(chunk_instance, landing)
                        
                        # Инвалидация кэша
                        cache_key = f"chunk_{landing.id}_{name}"
                        cache.delete(cache_key)
                
                # Проверка успешного создания истории
                if history and not history.id and is_dev():
                    logger.error(f"Не удалось сохранить историю чанка «{name}»")
                
                # Проверка наличия чанка
                if not chunk_instance and is_dev():
                    logger.error(f"Не найдено ни одного экземпляра чанка «{name}» для обновления")

            return chunk_instance
            
        except Exception as e:
            logger.error(f"Необработанная ошибка при обновлении чанка {name}: {str(e)}")
            return None

    @staticmethod
    def get_chunk(name: str) -> Optional[Chunk]:
        """Получить чанк
        
        :param name: Имя чанка
        :return: Экземпляр Chunk или None, если чанк не найден
        """
        try:
            from core.helpers import get_landing
            
            # Валидация входных данных
            if not name:
                logger.warning("Невозможно получить чанк: отсутствует имя чанка")
                return None
                
            landing = get_landing()
            if not landing:
                logger.warning("Невозможно получить чанк: не удалось получить лендинг")
                return None
            
            # Проверка кэша
            cache_key = f"chunk_{landing.id}_{name}"
            chunk = cache.get(cache_key)
            
            if chunk:
                return chunk
            
            # Получение из БД, если нет в кэше
            chunk = Chunk.objects.filter(
                name=name,
                landing=landing,
            ).first()
            
            # Кэширование результата
            if chunk:
                cache.set(cache_key, chunk, 3600)  # Кэшируем на час
                
            return chunk
            
        except Exception as e:
            logger.error(f"Ошибка при получении чанка {name}: {str(e)}")
            return None

    @staticmethod
    def share_chunks(landing: Optional[Landing] = None) -> None:
        """Загрузка всех чанков лендинга в глобальные переменные
        
        :param landing: Экземпляр лендинга или None для использования текущего
        """
        try:
            from core.chunks.helpers import add_chunk_to_globals
            from core.helpers import get_landing, get_current_host
            
            # Получение лендинга, если не указан
            landing = get_landing() if not landing else landing
            if not landing:
                logger.warning("Невозможно поделиться чанками: не удалось получить лендинг")
                return
                
            host_key = get_current_host(landing)
            
            # Инициализация глобальных переменных для хоста
            if host_key not in GLOBAL_VARS:
                GLOBAL_VARS[host_key] = {}
            
            # Оптимизированное получение всех чанков с использованием select_related
            chunks = Chunk.objects.filter(landing=landing).select_related()
            
            # Добавление чанков в глобальные переменные
            for chunk in chunks:
                add_chunk_to_globals(landing, chunk)
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке чанков в глобальные переменные: {str(e)}")
            
    @staticmethod
    def delete_chunk(name: str, landing: Optional[Landing] = None) -> bool:
        """Удаление чанка
        
        :param name: Имя чанка
        :param landing: Экземпляр лендинга или None для использования текущего
        :return: True в случае успеха, False в случае ошибки
        """
        try:
            from core.helpers import get_landing
            
            # Получение лендинга, если не указан
            landing = get_landing() if not landing else landing
            if not landing:
                logger.warning("Невозможно удалить чанк: не удалось получить лендинг")
                return False
                
            # Валидация входных данных
            if not name:
                logger.warning("Невозможно удалить чанк: отсутствует имя чанка")
                return False
                
            # Поиск чанка
            chunk = Chunk.objects.filter(
                name=name,
                landing=landing,
            ).first()
            
            if not chunk:
                logger.warning(f"Чанк {name} не найден для удаления")
                return False
                
            # Удаление чанка с использованием транзакции
            with transaction.atomic():
                # Удаление истории чанка
                ChunkHistory.objects.filter(chunk=chunk).delete()
                
                # Удаление самого чанка
                chunk.delete()
                
                # Инвалидация кэша
                cache_key = f"chunk_{landing.id}_{name}"
                cache.delete(cache_key)
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении чанка {name}: {str(e)}")
            return False
