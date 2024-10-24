from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"), # Стартовая страница со входом
    path("register/", views.register_view, name="register"), # Страница с регистрацией
    path("logout/", views.logout_view, name="logout"), # Путь выхода
    path("tasks/", views.task_list, name="task_list"), # Список задач
    path('create/', views.task_create, name='task_create'), # Создание задачи
    path('update/<int:task_id>/', views.task_update, name='task_update'), # Редактирование задачи
    path('delete/<int:task_id>/', views.task_delete, name='task_delete'), # Удаление задачи
    path('toggle/<int:task_id>/', views.toggle_task_completion, name='task_toggle_complete'), # Изменение галочки выполнено/не выполнено
]
