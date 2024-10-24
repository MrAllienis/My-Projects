from django import forms
from .models import Task, Category # Импорт созданных моделей
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User # Импорт стандартной модели пользователя

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'completed', 'category'] # Поля для редактирования

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs) # Вызов родительского конструктора, чтобы инициализировать форму.
        # Настройка атрибутов HTML для полей. Здесь мы добавляем CSS-класс form-control для стилизации с использованием Bootstrap.
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3}) # атрибут rows, который задает высоту текстового поля (число строк)
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
        self.fields['completed'].widget.attrs.update({'class': 'form-check-input'})


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"] # Поля для редактирования