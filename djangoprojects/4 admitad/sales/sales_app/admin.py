from django.contrib import admin
from .models import Shop, Product, Coupon, CategoryShop

# Register your models here.from django.contrib import admin

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'legal_info']
    list_display_links = ['name']
    search_fields = ['name', 'description']
    list_filter = ['name']
    readonly_fields = ('shop_id', 'legal_info', 'goto_link')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category1', 'shop']
    list_display_links = ['name']
    search_fields = ['name', 'shop__name']
    list_filter = ['shop']
    readonly_fields = ('url',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['discount', 'name', 'end_start', 'used', 'shop']
    list_display_links = ['name']
    search_fields = ['name', 'discount', 'shop__name']
    list_filter = ['discount', 'shop']
    readonly_fields = ('coupon_id','discount', 'end_start', 'shop')
    
@admin.register(CategoryShop)
class CategoryShopAdmin(admin.ModelAdmin):
    list_display = ['name']
