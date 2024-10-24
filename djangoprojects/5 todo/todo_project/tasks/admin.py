from django.contrib import admin
from .models import Task, Category # Импорт созданных моделей

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'user'] # Поля, отображаемые в админке в списке задач
    list_display_links = ['title'] # Поля, являющиеся ссылкой на задачу
    search_fields = ['title', 'description'] # Поля, участвующие в поиске
    list_filter = ['category']  # Фильтр
    readonly_fields = ('user', 'created_at', 'completed', 'category') # Не редактируемые поля


admin.site.register(Category)

