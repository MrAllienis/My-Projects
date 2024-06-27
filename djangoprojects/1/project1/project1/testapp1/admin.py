from django.contrib import admin
from .models import Mebel

# Register your models here.

class MebelAdmin(admin.ModelAdmin):
    list_display = ['id', 'price', 'parse_datetime', 'description']
    list_display_links = ['id', 'parse_datetime']
    search_fields = ['id', 'price', 'parse_datetime', 'description']
    list_editable = ['price']
    list_filter = ['parse_datetime', 'price']
    readonly_fields = ('parse_datetime',)


admin.site.register(Mebel, MebelAdmin)
