from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import JSONField


class Landing(models.Model):
    """
    Модель для лендингов (сайтов).
    Каждый лендинг представляет собой отдельный сайт с уникальным доменом.
    """
    name = models.CharField('Название', max_length=255)
    domain = models.CharField('Домен', max_length=255, unique=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # Дополнительное поле, используется для отслеживания, какое приложение использует лендинг
    app_name = models.CharField('Название приложения', max_length=100, default='default')

    class Meta:
        verbose_name = 'Лендинг'
        verbose_name_plural = 'Лендинги'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['app_name']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'https://{self.domain}/'


class Page(models.Model):
    """
    Модель для страниц лендинга.
    Каждая страница принадлежит определенному лендингу.
    """
    landing = models.ForeignKey(Landing, on_delete=models.CASCADE, related_name='pages', verbose_name='Лендинг')
    title = models.CharField('Заголовок', max_length=255)
    slug = models.SlugField('URL', max_length=255)
    content = models.TextField('Содержимое', blank=True)
    meta_description = models.TextField('Meta Description', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        ordering = ['landing', 'title']
        unique_together = ['landing', 'slug']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.landing.name} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'slug': self.slug})


class Chunk(models.Model):
    """
    Модель для хранения фрагментов контента (чанков).
    Чанки используются как строительные блоки для создания контента на лендингах.
    """
    landing = models.ForeignKey(Landing, on_delete=models.CASCADE, related_name='chunks', verbose_name='Лендинг')
    name = models.CharField('Название чанка', max_length=255)
    content = models.TextField('Содержимое', blank=True)
    custom_content = JSONField('Кастомное содержимое для страниц', default=dict, blank=True, null=True)
    through = models.BooleanField('Сквозной чанк', default=True, help_text='Если True, чанк отображается на всех страницах одинаково')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Чанк'
        verbose_name_plural = 'Чанки'
        ordering = ['landing', 'name']
        unique_together = ['landing', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['landing', 'name']),
        ]

    def __str__(self):
        return f'{self.landing.name} - {self.name}'

    def get_history(self):
        """Получить историю изменений чанка"""
        return self.history.all().order_by('-created_at')

    def get_last_update(self):
        """Получить последнее обновление чанка"""
        history = self.get_history().first()
        return history.created_at if history else self.updated_at


class ChunkHistory(models.Model):
    """
    Модель для хранения истории изменений чанков.
    Каждое изменение чанка сохраняется для возможности восстановления.
    """
    chunk = models.ForeignKey(Chunk, on_delete=models.CASCADE, related_name='history', verbose_name='Чанк')
    content = models.TextField('Содержимое', blank=True)
    custom_content = models.TextField('Кастомное содержимое', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кто создал')

    class Meta:
        verbose_name = 'История чанка'
        verbose_name_plural = 'История чанков'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chunk']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.chunk.name} - {self.created_at}'


class LocalLandingData(models.Model):
    """
    Модель для хранения локальных данных лендинга.
    Используется для A/B тестирования и сохранения временных изменений.
    """
    causer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='local_data', verbose_name='Пользователь')
    landing = models.ForeignKey(Landing, on_delete=models.CASCADE, related_name='local_data', verbose_name='Лендинг')
    temp_data = JSONField('Временные данные', default=dict)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Локальные данные лендинга'
        verbose_name_plural = 'Локальные данные лендингов'
        ordering = ['-updated_at']
        unique_together = ['causer', 'landing']
        indexes = [
            models.Index(fields=['causer']),
            models.Index(fields=['landing']),
        ]

    def __str__(self):
        return f'{self.landing.name} - {self.causer.username}'


class EList(models.Model):
    """
    Модель для хранения редактируемых списков.
    Используется для создания динамических списков элементов на лендингах.
    """
    landing = models.ForeignKey(Landing, on_delete=models.CASCADE, related_name='elists', verbose_name='Лендинг')
    name = models.CharField('Название списка', max_length=255)
    items = JSONField('Элементы списка', default=list)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Редактируемый список'
        verbose_name_plural = 'Редактируемые списки'
        ordering = ['landing', 'name']
        unique_together = ['landing', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['landing', 'name']),
        ]

    def __str__(self):
        return f'{self.landing.name} - {self.name}'