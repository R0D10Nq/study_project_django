from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from core.helpers import cache_page, chunk as core_chunk
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
import os

@ensure_csrf_cookie
@cache_page()
def example_page(request):
    # Базовый контекст для страницы
    context = {
        'page': {
            'title': core_chunk(name='pages.example_page.title', wrap=False),
            'description': core_chunk(name='pages.example_page.description', wrap=False),
        }
    }
    
    # Вместо загрузки модулей, просто выводим базовую HTML-страницу
    final_html = f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{context['page']['title']}</title>
        <meta name="description" content="{context['page']['description']}">
        <link rel="stylesheet" href="/static/css/styles.css">
    </head>
    <body>
        <header style="background-color: #f8f9fa; padding: 20px; text-align: center;">
            <h1>AllSmiles Redesign</h1>
            <p>Сайт успешно настроен!</p>
        </header>
        
        <main style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2>Модульная система</h2>
            <p>Для полноценной работы сайта необходимо настроить модульную систему с tpl.html.</p>
            <p>Модули находятся в директории:</p>
            <pre style="background-color: #f1f1f1; padding: 10px; border-radius: 5px;">modules/[module-name]/allsmiles_impl_redesign__blank__sinergium__ru/tpl.html</pre>
            
            <h3>Доступные модули:</h3>
            <ul style="list-style-type: disc; margin-left: 20px;">
                <li>m-header</li>
                <li>m-first-screen</li>
                <li>m-benefits</li>
                <li>m-implantation</li>
                <li>m-prosthesis</li>
                <li>m-diagnostics</li>
                <li>m-tomography</li>
                <li>m-reception</li>
                <li>m-employees</li>
                <li>m-works</li>
                <li>m-questions</li>
                <li>m-footer</li>
            </ul>
        </main>
        
        <footer style="background-color: #f8f9fa; padding: 20px; text-align: center; margin-top: 30px;">
            <p> 2025 AllSmiles Redesign</p>
        </footer>
        
        <script src="/static/js/main.js"></script>
    </body>
    </html>
    '''
    
    return HttpResponse(final_html)
