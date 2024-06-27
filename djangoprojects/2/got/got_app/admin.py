from django.contrib import admin
from .models import Character


class CharacterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','house_name', 'age']
    list_display_links = ['id', 'name','house_name']
    search_fields = ['id', 'name','house_name', 'age']
    list_filter = ['house_name', 'age', ]

# Register your models here.
admin.site.register(Character, CharacterAdmin)