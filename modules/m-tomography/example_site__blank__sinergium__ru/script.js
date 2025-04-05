/**
 * Скрипт модуля томографии
 * Отвечает за интерактивность модуля m-tomography
 */

class TomographyModule {
  constructor(selector = '.tomography') {
    this.container = document.querySelector(selector);
    
    if (!this.container) {
      console.warn('Модуль томографии не найден на странице');
      return;
    }
    
    this.videoElement = this.container.querySelector('video');
    this.lazyElements = this.container.querySelectorAll('[data-js="lazy"]');
    
    this.init();
  }
  
  init() {
    this.setupVideoAutoplay();
    this.setupIntersectionObserver();
    
    console.log('Модуль томографии инициализирован');
  }
  
  setupVideoAutoplay() {
    if (!this.videoElement) return;
    
    // Автовоспроизведение видео при попадании в область видимости
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.videoElement.play().catch(err => {
            console.warn('Автовоспроизведение видео заблокировано браузером:', err);
          });
        } else {
          this.videoElement.pause();
        }
      });
    }, { threshold: 0.3 });
    
    observer.observe(this.videoElement);
  }
  
  setupIntersectionObserver() {
    // Анимация появления элементов при скролле
    const animations = this.container.querySelectorAll('.tomography__item');
    
    if (!animations.length) return;
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          // Добавляем небольшую задержку для последовательной анимации
          setTimeout(() => {
            entry.target.classList.add('is-visible');
          }, index * 150);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });
    
    animations.forEach(item => {
      observer.observe(item);
    });
  }
}

// Инициализация модуля при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
  new TomographyModule();
});

export default TomographyModule;
