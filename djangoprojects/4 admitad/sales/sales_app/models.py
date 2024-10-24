from django.db import models
from django.utils import timezone

from django.contrib.postgres.search import SearchVectorField

# Create your models here.



class CategoryShop(models.Model):
    id = models.CharField('ID', unique=True, primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Категория магазинов'
        verbose_name_plural = 'Категории магазинов'
        ordering = ['name']
        

class Shop(models.Model):
    shop_id = models.IntegerField('ID', unique=True, primary_key=True)
    category = models.ManyToManyField(CategoryShop, related_name='shops')
    name = models.CharField('Название', max_length=255)
    goto_link = models.URLField('Реферальная ссылка', max_length=1000, null=True, blank=True)
    legal_info = models.TextField('О рекламодателе', null=True, blank=True)
    image = models.URLField('Логотип', max_length=2000, null=True, blank=True)
    csv_link = models.URLField('Товары в CSV', max_length=2000, null=True, blank=True)
    xml_link = models.URLField('Товары в XML', max_length=2000, null=True, blank=True)
    description = models.TextField('Описание', null=True, blank=True)
    last_update = models.DateTimeField('Дата обновления товаров', null=True, blank=True)

    def __str__(self):
        return f'{self.name} | {self.legal_info}'
    
    def get_absolute_url(self):
        return self.goto_link

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ['name']


class Product(models.Model):
    id = models.CharField('ID', unique=True, primary_key=True)
    image = models.URLField('Фото', max_length=2000, null=True, blank=True)
    url = models.URLField('Ссылка на товар', max_length=2000, null=True, blank=True)
    name = models.CharField('Название', max_length=500, db_index=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    old_price = models.DecimalField('Старая цена',max_digits=10, decimal_places=2, null=True, blank=True)
    sale = models.IntegerField('Скидка', null=True, blank=True)
    category1 = models.CharField('Категория',max_length=255, null=True, blank=True)
    shop = models.ForeignKey(Shop, related_name='products', on_delete=models.CASCADE, db_index=True)
    used = models.BooleanField('Пост опубликован', default=False)
    chat_id = models.BigIntegerField('CHAT_ID', null=True, blank=True)
    message_id = models.BigIntegerField('MESSAGE_ID', null=True, blank=True)
    search = SearchVectorField(null=True, blank=True)


    def __str__(self):
        return f'{self.name} | {self.price} RUB | {self.category1}'
    
    def get_absolute_url(self):
        return self.url

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name', 'price', 'shop', 'category1']
        
        

class Coupon(models.Model):
    coupon_id = models.IntegerField('ID', unique=True, primary_key=True)
    image = models.URLField('Фото', max_length=2000, null=True, blank=True)
    shop = models.ForeignKey(Shop, related_name='promocodes', on_delete=models.CASCADE)
    discount = models.CharField('Скидка', max_length=10, null=True, blank=True)
    name = models.TextField('Название')
    condition = models.TextField('Условие купона', null=True, blank=True)
    date_start = models.DateTimeField('Дата начала действия')
    end_start = models.DateTimeField('Дата окончания действия', null=True, blank=True)
    code = models.CharField('Промокод', max_length=50)
    used = models.BooleanField('Пост опубликован', default=False)
    chat_id = models.BigIntegerField('CHAT_ID', null=True, blank=True)
    message_id = models.BigIntegerField('MESSAGE_ID', null=True, blank=True)
    link = models.URLField('Ссылка на купон', max_length=2000, null=True, blank=True)
    
    def __str__(self):
        return f'{self.name} | {self.shop} | {self.code}'

    
    class Meta:
        verbose_name = 'Купон/промокод'
        verbose_name_plural = 'Купоны и промокоды'
        ordering = ['discount', 'shop', 'end_start']


class LinkClick(models.Model):
    yclid = models.BigIntegerField(unique=True)
    clicked_at = models.DateTimeField(default=timezone.now)
    goal_at = models.DateTimeField(blank=True, null=True)
    tg_id = models.BigIntegerField(blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.BigIntegerField(blank=True, null=True)
    client_id = models.BigIntegerField(blank=True, null=True)
    conversion = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.yclid} - {self.clicked_at} - {self.goal_at} - {self.conversion}"



