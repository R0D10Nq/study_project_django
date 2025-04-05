/**
 * Главный файл скриптов для лэндинга example_site__blank__sinergium__ru
 * Здесь импортируются все модульные скрипты и инициализируется общая функциональность
 */

// Импорт базовых компонентов
import '../../../../core/static/js/base';
import LazyLoad from '../../../../core/static/js/lazy-load';

// Импорт модульных скриптов
import '../../../../modules/m-tomography/example_site__blank__sinergium__ru/script';

// Инициализация общих компонентов
document.addEventListener('DOMContentLoaded', () => {
    // Инициализация ленивой загрузки изображений
    const lazyLoad = new LazyLoad('[data-js="lazy"]');
    
    // Другие инициализации...
    
    console.log('Лэндинг example_site__blank__sinergium__ru успешно инициализирован');
});
