@echo off
echo Запуск в режиме разработки...

REM Устанавливаем переменные окружения
set DEBUG=True
set DJANGO_SETTINGS_MODULE=settings

REM Запускаем сервер разработки
python manage.py runserver

echo Сервер остановлен.
