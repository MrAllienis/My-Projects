from django.db import models
from django.contrib.auth.models import User # Импорт стандартной модели пользователя

class Category(models.Model):
    name = models.CharField('Категория', max_length=100, unique=True) # Уникальное значение, макс. количество символов = 100

    def __str__(self):
        return self.name # Отображение поля name

    class Meta:
        verbose_name = 'Категория' # Название в ед.ч.
        verbose_name_plural = 'Категории' # Название во мн.ч.
        ordering = ['name'] # Сортировка по полю name

class Task(models.Model):
    title = models.CharField('Название', max_length=200)
    description = models.TextField( 'Описание', blank=True)
    completed = models.BooleanField('Выполнено', default=False) # Колонка со значением выполнено/не выполнено. По умолчанию НЕ выполнено
    created_at = models.DateTimeField('Дата создания', auto_now_add=True) # Дата и время создания задачи. Автоматически заполняется настоящими датой и временем
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True, verbose_name='Категория') # Вторичный ключ на модель категории
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks') # Вторичный ключ на стандартную модель User

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['created_at']
