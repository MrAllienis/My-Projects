from django.db import models

# Create your models here.
class Mebel(models.Model):
    link = models.TextField('Link')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')
    description = models.TextField(verbose_name='Описание с Куфара')
    parse_datetime = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        verbose_name='Дата и время добавления'
    )

    def get_absolute_url(self):
        return self.link

    def __str__(self):
        return f'{self.price} | {self.description[:60]}'

    class Meta:
        verbose_name = 'Мебель'
        verbose_name_plural = 'Мебель'
        ordering = ['parse_datetime', 'price']





