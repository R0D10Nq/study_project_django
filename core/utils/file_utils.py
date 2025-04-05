"""
Утилиты для работы с файлами и изображениями
"""
import os
import hashlib
import subprocess
import stat
from PIL import Image, ImageOps, ImageSequence
import pillow_heif
from pathlib import Path
from core.settings import BASE_DIR, MEDIA_URL

def file_get_contents(filename):
    """
    Прочесть содержимое файла
    :param filename: Путь к файлу
    :return: str
    """
    if not os.path.exists(filename):
        return ""
    
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def replace_in_file(file, needle: str, replacement: str):
    """
    Заменить вхождение в файле
    :param file: Путь к файлу
    :param needle: Что ищем
    :param replacement: На что заменить
    :return: bool
    """
    if not os.path.exists(file):
        return False
    
    # Читаем содержимое файла
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Заменяем вхождение
    content = content.replace(needle, replacement)
    
    # Записываем обратно
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


def make_img_plug(name, width, height, module_path=None, custom_plug=None):
    """
    Генерируем плейсхолдер для изображения, если никакого не нашли
    :param name: Имя изображения
    :param width: Ширина
    :param height: Высота
    :param module_path: Папка модуля
    :param custom_plug: Кастомное название для файла plug
    :return: str
    """
    # Формируем путь к изображению
    if module_path:
        # Если указан путь к модулю
        img_path = os.path.join(module_path, "static", "img", name)
    else:
        # Иначе ищем в корне проекта
        img_path = os.path.join(BASE_DIR, "static", "img", name)
    
    # Проверяем существование изображения
    if os.path.exists(img_path):
        # Если изображение существует, возвращаем его путь
        return f"{MEDIA_URL}img/{name}"
    
    # Иначе возвращаем плейсхолдер
    return f"https://via.placeholder.com/{width}x{height}"


def get_file_hash(file_path):
    """
    Получить хеш файла
    :param file_path: Путь к файлу
    :return: str
    """
    if not os.path.exists(file_path):
        return ""
    
    # Вычисляем хеш файла
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    
    return file_hash.hexdigest()


def convert_size(size_bytes):
    """
    Человекопонятный размер файла
    :param size_bytes: Размер в байтах
    :return: str
    """
    if size_bytes == 0:
        return "0B"
    
    # Суффиксы размеров
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    
    # Вычисляем индекс суффикса
    i = int(math.floor(math.log(size_bytes, 1024)))
    
    # Форматируем размер
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_name[i]}"


def exec_command(command: str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    """
    Выполнить команду в терминале
    :param command: Команда
    :param shell: Использовать shell
    :param stdout: Стандартный вывод
    :param stderr: Стандартный вывод ошибок
    :return: tuple
    """
    # Выполняем команду
    process = subprocess.Popen(command, shell=shell, stdout=stdout, stderr=stderr)
    
    # Получаем результат
    stdout, stderr = process.communicate()
    
    return stdout, stderr, process.returncode


# Импортируем необходимые модули
import math
