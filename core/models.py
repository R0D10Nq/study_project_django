from django.db import models
from django.utils.text import slugify
from django.urls import reverse


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

    class Meta:
        verbose_name = 'Лендинг'
        verbose_name_plural = 'Лендинги'
        ordering = ['-created_at']

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
    slug = models.SlugField('URL', max_length=255, unique=True)
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

    def __str__(self):
        return f'{self.landing.name} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'slug': self.slug})