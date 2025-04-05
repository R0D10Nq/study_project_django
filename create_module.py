#!/usr/bin/env python
"""
Скрипт для быстрого создания новых модулей
Использование: python create_module.py название_модуля
"""
import os
import sys
import shutil
from pathlib import Path

def create_module(module_name):
    """
    Создает новый модуль на основе шаблона
    :param module_name: Название модуля
    """
    # Проверяем, что название начинается с m-
    if not module_name.startswith("m-"):
        module_name = f"m-{module_name}"
    
    # Пути к директориям
    base_dir = Path(__file__).resolve().parent
    template_dir = os.path.join(base_dir, "modules", "_template")
    module_dir = os.path.join(base_dir, "modules", module_name)
    
    # Проверяем существование директории
    if os.path.exists(module_dir):
        print(f"Ошибка: Модуль {module_name} уже существует")
        return False
    
    # Проверяем существование шаблона
    if not os.path.exists(template_dir):
        print("Ошибка: Шаблон модуля не найден")
        return False
    
    # Копируем шаблон
    shutil.copytree(template_dir, module_dir)
    
    # Заменяем название модуля в файлах
    replace_in_files(module_dir, "module-template", f"module-{module_name}")
    
    print(f"Модуль {module_name} успешно создан в {module_dir}")
    print("Не забудьте отредактировать README.md и template.html")
    
    return True


def replace_in_files(directory, old_text, new_text):
    """
    Заменяет текст во всех файлах директории
    :param directory: Путь к директории
    :param old_text: Старый текст
    :param new_text: Новый текст
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".html", ".css", ".js", ".md")):
                file_path = os.path.join(root, file)
                
                # Читаем содержимое
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Заменяем текст
                content = content.replace(old_text, new_text)
                
                # Записываем обратно
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)


if __name__ == "__main__":
    # Проверяем аргументы
    if len(sys.argv) < 2:
        print("Использование: python create_module.py название_модуля")
        sys.exit(1)
    
    # Создаем модуль
    create_module(sys.argv[1])
