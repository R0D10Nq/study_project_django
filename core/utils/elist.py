"""
Модуль для работы с редактируемыми списками (EditableList)
Предоставляет интерфейс для управления динамическими списками данных.
"""
import json
import logging
from django.core.cache import cache
from django.utils.safestring import mark_safe
from core.models import EList

logger = logging.getLogger('chunks')

class EditableList:
    """
    Класс для работы с редактируемыми списками.
    Позволяет создавать, редактировать и отображать динамические списки данных.
    """
    def __init__(self, name, landing=None, items=None, template='default'):
        """
        Инициализация редактируемого списка.
        
        :param name: Уникальное имя списка
        :param landing: Связанный лендинг (опционально)
        :param items: Начальные элементы списка (опционально)
        :param template: Шаблон для отображения (default, table, cards, slider)
        """
        self.name = name
        self.landing = landing
        self.items = items or []
        self.template = template
        self._loaded = False
        
    def load(self):
        """
        Загружает данные списка из базы данных или кэша.
        
        :return: self для цепочки вызовов
        """
        if self._loaded:
            return self
            
        cache_key = f"elist_{self.name}"
        if self.landing:
            cache_key += f"_{self.landing.id}"
            
        # Пробуем загрузить из кэша
        cached_data = cache.get(cache_key)
        if cached_data:
            self.items = cached_data.get('items', [])
            self.template = cached_data.get('template', self.template)
            self._loaded = True
            return self
            
        # Если нет в кэше, загружаем из БД
        try:
            if self.landing:
                elist = EList.objects.get(name=self.name, landing=self.landing)
            else:
                elist = EList.objects.get(name=self.name, landing__isnull=True)
                
            self.items = json.loads(elist.data) if elist.data else []
            self.template = elist.template
            
            # Кэшируем результат
            cache.set(cache_key, {
                'items': self.items,
                'template': self.template
            }, 3600)  # Кэшируем на 1 час
            
        except EList.DoesNotExist:
            # Если списка нет в БД, создаем новый
            self._create_new()
            
        except Exception as e:
            logger.error(f"Error loading EList {self.name}: {str(e)}")
            
        self._loaded = True
        return self
        
    def _create_new(self):
        """
        Создает новый список в базе данных.
        """
        try:
            elist = EList(
                name=self.name,
                landing=self.landing,
                data=json.dumps(self.items),
                template=self.template
            )
            elist.save()
            
            # Кэшируем новый список
            cache_key = f"elist_{self.name}"
            if self.landing:
                cache_key += f"_{self.landing.id}"
                
            cache.set(cache_key, {
                'items': self.items,
                'template': self.template
            }, 3600)
            
        except Exception as e:
            logger.error(f"Error creating EList {self.name}: {str(e)}")
            
    def add(self, item):
        """
        Добавляет элемент в список.
        
        :param item: Элемент для добавления
        :return: self для цепочки вызовов
        """
        self.load()
        self.items.append(item)
        self._save()
        return self
        
    def remove(self, index):
        """
        Удаляет элемент из списка по индексу.
        
        :param index: Индекс элемента для удаления
        :return: self для цепочки вызовов
        """
        self.load()
        if 0 <= index < len(self.items):
            del self.items[index]
            self._save()
        return self
        
    def update(self, index, item):
        """
        Обновляет элемент в списке по индексу.
        
        :param index: Индекс элемента для обновления
        :param item: Новое значение элемента
        :return: self для цепочки вызовов
        """
        self.load()
        if 0 <= index < len(self.items):
            self.items[index] = item
            self._save()
        return self
        
    def clear(self):
        """
        Очищает список.
        
        :return: self для цепочки вызовов
        """
        self.load()
        self.items = []
        self._save()
        return self
        
    def _save(self):
        """
        Сохраняет изменения в базе данных и обновляет кэш.
        """
        try:
            # Обновляем в БД
            if self.landing:
                elist, created = EList.objects.get_or_create(
                    name=self.name,
                    landing=self.landing,
                    defaults={'template': self.template}
                )
            else:
                elist, created = EList.objects.get_or_create(
                    name=self.name,
                    landing__isnull=True,
                    defaults={'template': self.template}
                )
                
            elist.data = json.dumps(self.items)
            elist.template = self.template
            elist.save()
            
            # Обновляем кэш
            cache_key = f"elist_{self.name}"
            if self.landing:
                cache_key += f"_{self.landing.id}"
                
            cache.set(cache_key, {
                'items': self.items,
                'template': self.template
            }, 3600)
            
        except Exception as e:
            logger.error(f"Error saving EList {self.name}: {str(e)}")
            
    def render(self, template=None):
        """
        Отображает список согласно выбранному шаблону.
        
        :param template: Шаблон для отображения (переопределяет self.template)
        :return: HTML для отображения списка
        """
        self.load()
        template_to_use = template or self.template
        
        # Здесь должна быть логика рендеринга в зависимости от шаблона
        if template_to_use == 'table':
            return self._render_table()
        elif template_to_use == 'cards':
            return self._render_cards()
        elif template_to_use == 'slider':
            return self._render_slider()
        elif template_to_use == 'tabs':
            return self._render_tabs()
        else:
            return self._render_default()
            
    def _render_default(self):
        """
        Отображает список в виде простого списка.
        
        :return: HTML для отображения списка
        """
        html = '<ul class="elist elist-default">'
        for item in self.items:
            html += f'<li>{item}</li>'
        html += '</ul>'
        return mark_safe(html)
        
    def _render_table(self):
        """
        Отображает список в виде таблицы.
        
        :return: HTML для отображения списка
        """
        html = '<table class="elist elist-table"><tbody>'
        for item in self.items:
            if isinstance(item, dict):
                html += '<tr>'
                for key, value in item.items():
                    html += f'<td>{value}</td>'
                html += '</tr>'
            else:
                html += f'<tr><td>{item}</td></tr>'
        html += '</tbody></table>'
        return mark_safe(html)
        
    def _render_cards(self):
        """
        Отображает список в виде карточек.
        
        :return: HTML для отображения списка
        """
        html = '<div class="elist elist-cards">'
        for item in self.items:
            if isinstance(item, dict):
                html += '<div class="elist-card">'
                for key, value in item.items():
                    html += f'<div class="elist-card-{key}">{value}</div>'
                html += '</div>'
            else:
                html += f'<div class="elist-card">{item}</div>'
        html += '</div>'
        return mark_safe(html)
        
    def _render_slider(self):
        """
        Отображает список в виде слайдера.
        
        :return: HTML для отображения списка
        """
        html = '<div class="elist elist-slider"><div class="elist-slider-container">'
        for item in self.items:
            if isinstance(item, dict):
                html += '<div class="elist-slide">'
                for key, value in item.items():
                    html += f'<div class="elist-slide-{key}">{value}</div>'
                html += '</div>'
            else:
                html += f'<div class="elist-slide">{item}</div>'
        html += '</div></div>'
        return mark_safe(html)
        
    def _render_tabs(self):
        """
        Отображает список в виде вкладок.
        
        :return: HTML для отображения списка
        """
        html = '<div class="elist elist-tabs"><div class="elist-tabs-header">'
        
        # Заголовки вкладок
        for i, item in enumerate(self.items):
            title = item.get('title', f'Вкладка {i+1}') if isinstance(item, dict) else f'Вкладка {i+1}'
            active = ' active' if i == 0 else ''
            html += f'<div class="elist-tab-title{active}" data-tab="{i}">{title}</div>'
        
        html += '</div><div class="elist-tabs-content">'
        
        # Содержимое вкладок
        for i, item in enumerate(self.items):
            active = ' active' if i == 0 else ''
            html += f'<div class="elist-tab-content{active}" data-tab="{i}">'
            
            if isinstance(item, dict):
                for key, value in item.items():
                    if key != 'title':
                        html += f'<div class="elist-tab-{key}">{value}</div>'
            else:
                html += f'{item}'
                
            html += '</div>'
            
        html += '</div></div>'
        return mark_safe(html)
        
    def __iter__(self):
        """
        Позволяет перебирать элементы списка в цикле.
        
        :return: Итератор по элементам списка
        """
        self.load()
        return iter(self.items)
        
    def __getitem__(self, index):
        """
        Позволяет получать элементы списка по индексу.
        
        :param index: Индекс элемента
        :return: Элемент списка
        """
        self.load()
        return self.items[index]
        
    def __len__(self):
        """
        Возвращает длину списка.
        
        :return: Количество элементов в списке
        """
        self.load()
        return len(self.items)
