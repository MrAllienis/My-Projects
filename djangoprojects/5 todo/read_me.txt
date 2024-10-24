Создания приложения "To-Do" в Django с возможностью регистрации пользователей. В самом коде также имеются комментарии, обозначенные #

- Установка Django и создание проекта в терминале
    pip install django
    django-admin startproject todo_project

- Создание приложения "tasks" в папке проекта
    cd todo_project
    python manage.py startapp tasks

- Добавление приложения в INSTALLED_APPS в файле settings.py:
    INSTALLED_APPS = [
        # другие приложения
        'tasks',
    ]

- В файле settings.py меняем часовой пояс на московское время и язык на русский
    TIME_ZONE = 'Europe/Moscow'
    LANGUAGE_CODE = 'ru-ru'

- Создание админ-аккаунта для админки. Главное указать логин и пароль
    python manage.py createsuperuser

- Продумка базы данных, создание моделей в файле models.py
    - Создаем модели категорий и задач
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

- После создания моделей делаем миграции в терминале
    python manage.py makemigrations tasks
    python manage.py migrate

- Настройка файла админки admin.py
    from .models import Task, Category # Импорт созданных моделей

    @admin.register(Task)
    class TaskAdmin(admin.ModelAdmin):
        list_display = ['title', 'created_at', 'user'] # Поля, отображаемые в админке в списке задач
        list_display_links = ['title'] # Поля, являющиеся ссылкой на задачу
        search_fields = ['title', 'description'] # Поля, участвующие в поиске
        list_filter = ['category']  # Фильтр
        readonly_fields = ('user', 'created_at', 'completed', 'category') # Не редактируемые поля

    admin.site.register(Category)


- Создаем формы для редактирования на сайте задач, регистрации. Создаем файл tasks/forms.py.
    - TaskForm наследует от forms.ModelForm, что позволяет автоматически создавать форму на основе модели. Django использует информацию о модели для создания полей формы, соответствующих полям модели.

        class TaskForm(forms.ModelForm):
        class Meta:
            model = Task
            fields = ['title', 'description', 'completed', 'category'] # Поля для редактирования

    - Метод __init__ вызывается при создании экземпляра формы. Здесь происходит переопределение конструктора базового класса ModelForm, чтобы можно было кастомизировать форму.

        def __init__(self, *args, **kwargs):
            super(TaskForm, self).__init__(*args, **kwargs) # Вызов родительского конструктора, чтобы инициализировать форму.
            # Настройка атрибутов HTML для полей. Здесь мы добавляем CSS-класс form-control для стилизации с использованием Bootstrap.
            self.fields['title'].widget.attrs.update({'class': 'form-control'})
            self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3}) # атрибут rows, который задает высоту текстового поля (число строк)
            self.fields['category'].widget.attrs.update({'class': 'form-control'})
            self.fields['completed'].widget.attrs.update({'class': 'form-check-input'})

        class RegisterForm(UserCreationForm):
        # RegisterForm наследуется от UserCreationForm, которая представляет собой стандартную форму Django для создания нового пользователя. Она включает поля для имени пользователя и пароля, а также встроенные проверки.
            email = forms.EmailField(required=True)
            # поле email, которое не входит в стандартный набор полей UserCreationForm. Это поле является обязательным (required=True), и его тип — EmailField, что обеспечивает автоматическую проверку введенного значения на соответствие формату электронной почты.


- В папке todo_project создаем папку templates, где будут храниться наши шаблоны html
- В файле settings.py в TEMPLATES делаем
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
- В папке templates создаём файл base.html и папку tasks, в которой создаем файлы: login.html, register.html, task_form.html, task_list.html
- Опишем вьюхи(представления) для отображения списка задач, создания, редактирования и удаления задач в файле views.py
    - Функция регистрации

        def register_view(request):
        if request.method == "POST":
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                return redirect("task_list")
        else:
            form = RegisterForm()
        return render(request, "tasks/register.html", {"form": form})

        Проверка метода запроса (POST или GET): Если request.method == "POST", это значит, что пользователь отправил данные формы для регистрации.
        Если метод не POST, то запрос будет обработан как GET, что означает, что пользователь просто открыл страницу регистрации.
        Создание и проверка формы: form = RegisterForm(request.POST): Создается экземпляр формы регистрации RegisterForm, который заполняется данными из request.POST.
        if form.is_valid(): Проверяет, прошли ли данные формы валидацию (например, совпадение паролей, уникальность имени пользователя и т.д.).
        Создание пользователя и вход в систему: user = form.save(): Если форма прошла проверку, создается новый пользователь в базе данных.
        login(request, user): Пользователь автоматически аутентифицируется (вход в систему сразу после регистрации).
        return redirect("task_list"): Перенаправление пользователя на страницу списка задач (task_list) после успешной регистрации и входа.
        Обработка GET запроса: form = RegisterForm(): Создается пустая форма, которая будет отображаться на странице регистрации.
        Отображение шаблона: return render(request, "tasks/register.html", {"form": form}): Рендерит шаблон register.html с формой регистрации.

    - Функция входа
        def login_view(request):
            if request.method == "POST":
                form = AuthenticationForm(request, data=request.POST)
                if form.is_valid():
                    username = form.cleaned_data.get("username")
                    password = form.cleaned_data.get("password")
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        login(request, user)
                        return redirect("task_list")
            else:
                form = AuthenticationForm()
            return render(request, "tasks/login.html", {"form": form})

        Проверка метода запроса (POST или GET):

        Если запрос POST, то пользователь отправил данные формы для входа.
        Если запрос GET, то пользователь просто открыл страницу входа.
        Создание и проверка формы: form = AuthenticationForm(request, data=request.POST): Создается экземпляр формы аутентификации AuthenticationForm, который принимает данные запроса.
        if form.is_valid(): Проверяет корректность введенных данных (например, правильность имени пользователя и пароля).
        Аутентификация пользователя: username = form.cleaned_data.get("username") и password = form.cleaned_data.get("password"): Получение данных формы.
        user = authenticate(username=username, password=password): Проверяет, существуют ли пользователь с таким именем и паролем в базе данных.
        if user is not None: Если пользователь существует, происходит вход в систему.
        login(request, user): Авторизует пользователя в системе.
        return redirect("task_list"): Перенаправляет пользователя на страницу списка задач после успешного входа.
        Обработка GET запроса: form = AuthenticationForm(): Создается пустая форма для отображения на странице входа.
        Отображение шаблона: return render(request, "tasks/login.html", {"form": form}): Рендерит шаблон login.html с формой входа.

    - Функция выхода
        def logout_view(request):
            logout(request)
            return redirect("login")

        logout(request): Функция logout разлогинивает текущего пользователя.
        Перенаправление на страницу входа: return redirect("login")


    - Следующие функции представляют основные CRUD-операции (создание, чтение, обновление и удаление) для управления задачами
    - @login_required: Этот декоратор проверяет, авторизован ли пользователь. Если нет, то он перенаправляется на страницу входа. Таким образом, доступ к задачам и их изменениям имеют только авторизованные пользователи.

    - Функция task_list

        @login_required
        def task_list(request):
            tasks = Task.objects.filter(user=request.user)
            return render(request, "tasks/task_list.html", {"tasks": tasks})

        Фильтрация задач по текущему пользователю: Task.objects.filter(user=request.user): Получает задачи, связанные с текущим авторизованным пользователем (request.user). Это обеспечивает отображение только тех задач, которые принадлежат текущему пользователю.
        Отображение шаблона task_list.html: render(request, "tasks/task_list.html", {"tasks": tasks}): Рендерит страницу со списком задач, передавая в контекст задачи, отфильтрованные по пользователю.

    - Функция task_create

        @login_required
        def task_create(request):
            if request.method == 'POST':
                form = TaskForm(request.POST)
                if form.is_valid():
                    task = form.save(commit=False)  # Создаем объект, но не сохраняем его в базе данных
                    task.user = request.user        # Присваиваем текущего пользователя
                    task.save()                     # Сохраняем объект с привязкой к пользователю
                    return redirect('task_list')
            else:
                form = TaskForm()
            return render(request, 'tasks/task_form.html', {'form': form})

        Проверка метода запроса: Если request.method == 'POST', пользователь отправляет форму создания задачи. В противном случае, форма просто отображается.
        Создание формы: form = TaskForm(request.POST): Если запрос POST, создается экземпляр формы с переданными данными.
        form = TaskForm(): Если запрос GET, создается пустая форма для отображения на странице.
        Проверка формы на валидность и сохранение задачи: if form.is_valid(): Проверяет, корректны ли введенные данные.
        task = form.save(commit=False): Создает объект задачи, но не сохраняет его сразу в базу данных.
        task.user = request.user: Привязывает задачу к текущему пользователю.
        task.save(): Сохраняет задачу в базу данных с привязкой к пользователю.
        return redirect('task_list'): Перенаправляет пользователя на страницу со списком задач.
        Рендеринг формы: render(request, 'tasks/task_form.html', {'form': form}): Отображает форму на странице.

    - Функция task_update

        @login_required
        def task_update(request, task_id):
            task = get_object_or_404(Task, id=task_id)
            if request.method == 'POST':
                form = TaskForm(request.POST, instance=task)
                if form.is_valid():
                    form.save()
                    return redirect('task_list')
            else:
                form = TaskForm(instance=task)
            return render(request, 'tasks/task_form.html', {'form': form})

        Получение задачи по task_id: task = get_object_or_404(Task, id=task_id): Получает задачу из базы данных или возвращает ошибку 404, если задача не найдена.
        Проверка метода запроса и обработка формы:
        if request.method == 'POST': Если запрос POST, обновляются данные задачи.
        form = TaskForm(request.POST, instance=task): Форма создается с переданными данными и привязана к существующей задаче.
        form = TaskForm(instance=task): Если запрос GET, форма заполняется текущими данными задачи.
        Сохранение обновленных данных:
        if form.is_valid(): Проверяет валидность данных формы.
        form.save(): Сохраняет обновленные данные.
        Перенаправление и отображение формы:
        return redirect('task_list'): Перенаправляет на страницу задач после успешного обновления.
        render(request, 'tasks/task_form.html', {'form': form}): Отображает форму с текущими данными задачи.

    - Функция task_delete

        @login_required
        def task_delete(request, task_id):
            task = get_object_or_404(Task, id=task_id)
            if request.method == 'POST':
                task.delete()
                return redirect('task_list')

        Получение задачи по task_id: task = get_object_or_404(Task, id=task_id): Проверяет существование задачи.
        Удаление задачи при подтверждении POST запроса: if request.method == 'POST': Удаление задачи происходит только при отправке формы подтверждения.
        task.delete(): Удаляет задачу из базы данных.
        return redirect('task_list'): Перенаправляет на список задач после удаления.

    - Функция toggle_task_completion

        @login_required
        def toggle_task_completion(request, task_id):
            task = get_object_or_404(Task, id=task_id)
            task.completed = not task.completed  # Переключаем статус
            task.save()
            return redirect('task_list')

        Получение задачи по task_id:
        task = get_object_or_404(Task, id=task_id): Проверяет существование задачи.
        Переключение статуса задачи:
        task.completed = not task.completed: Переключает значение поля completed на противоположное (если задача была завершена, то становится незавершенной и наоборот).
        task.save(): Сохраняет изменения в базе данных.
        return redirect('task_list'): Перенаправляет на страницу со списком задач после изменения статуса.



- Настроим маршруты, ссылающиеся на представления, для нашего приложения в файле tasks/urls.py, предварительно создав его

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

- Настроим маршруты проекта в todo_project/urls.py

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('tasks.urls')), # Использование маршрутов в файле tasks/urls.py
    ]


- Коротко о шаблонах
    - base.html
        Общий шаблон для всех шаблонов.
        <meta name="viewport" content="width=device-width, initial-scale=1.0">: Этот мета-тег управляет тем, как страница отображается на мобильных устройствах.
        <link href="https://cdK2Kadq2F9CUG6...... Подключает CSS-файл Bootstrap, который предоставляет стили для элементов HTML, таких как кнопки, формы и сетка.
        <body>: Начало основной части документа, где размещается всё видимое содержимое страницы.
        <div class="container mt-5">: Используется класс container Bootstrap для создания отступов и центрирования контента. Класс mt-5 добавляет верхний отступ (margin-top) размером 5 (в соответствии с сеткой Bootstrap).
        {% block content %} {% endblock %}: Это специальная конструкция Django (шаблонный тег), которая определяет область для вставки контента в дочерние шаблоны. Когда вы создаете другие страницы, вы можете расширить этот базовый шаблон и вставить свой контент в этот блок.
        <!-- Подключение Bootstrap JS -->
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.0.7/dist/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>

    - register.html
        {% extends 'base.html' %}: Этот тег говорит, что данный шаблон наследует структуру базового шаблона base.html. Это означает, что весь контент, определенный в базовом шаблоне, будет доступен, и вы можете добавлять или переопределять блоки, такие как content.
        {% block content %}: Открывает блок контента, который будет заменен или дополнен содержимым этого шаблона при его рендеринге.
        <form method="post">: Определяет форму, которая будет отправляться методом POST. Это важно для безопасности, так как данные, введенные пользователем, не будут отображаться в URL.
        {% csrf_token %}: Включает токен CSRF (Cross-Site Request Forgery), который предотвращает атаки, связанные с подделкой запросов. Это обязательный шаг для форм, обрабатывающих данные.
        {{ form.as_p }}: Генерирует HTML для полей формы. as_p отображает каждое поле формы в отдельном <p>-теге, что упрощает стилизацию и делает код более читаемым.
        {% endblock %}: Закрывает блок content. Всё содержимое между {% block content %} и {% endblock %} будет добавлено в основной шаблон на месте вызова блока.

    - login.html
        <p>Нет аккаунта? <a href="{% url 'register' %}" class="btn btn-link">Зарегистрироваться</a></p> Ссылка перенаправления на страницу регистрации

    - task_list.html
        <h4 class="mr-3">{{ request.user.username }}</h4>: Отображает имя текущего пользователя.
        <a href="{% url 'logout' %}" class="btn btn-danger" style="margin-left: 5px">Выйти</a>: Кнопка выхода, которая перенаправляет пользователя на URL, связанный с представлением выхода. Кнопка стилизована с помощью Bootstrap, чтобы выглядеть как кнопка с красным фоном (danger).
        <a href="{% url 'task_create' %}" class="btn btn-primary">Добавить задачу</a>: Кнопка для создания новой задачи
        {% if tasks %}: Проверяет, есть ли задачи для отображения.
        {% for task in tasks %}: Итерация по всем задачам, которые были переданы в контексте шаблона.
        <strong><a href="{% url 'task_update' task.id %}" class="text-dark">{{ task.title }}</a></strong>: Заголовок задачи, который является ссылкой для редактирования.
        {% if task.category %}: Проверяет, есть ли категория, связанная с задачей. Если да, то отображает её.
        {% if task.completed %}: Проверяет, выполнена ли задача, и отображает соответствующий текст.
        action="{% url 'task_toggle_complete' task.id %}": Указывает, куда будет отправлен запрос (для переключения статуса завершенности задачи).
        <input type="checkbox">: Чекбокс для изменения статуса задачи. Он отправляет форму при изменении состояния.
        {% csrf_token %}: Защита от CSRF.
        action="{% url 'task_delete' task.id %}": Указывает, куда будет отправлен запрос для удаления задачи.
        onsubmit="return confirmDelete();: Вызывает функцию confirmDelete(), чтобы подтвердить удаление.
        <script>: Скрипт JS, который вызывает окно подтверждения перед удалением задачи.
        <style>: Использование встроенных CSS стилей

    - task_form.html
        <label for="{{ form.title.id_for_label }}">{{ form.title.label }}</label>: Создает метку для поля заголовка, связывая её с элементом формы через атрибут for.
        {{ form.title }}: Отображает элемент формы для заголовка.
        {{ form.title.errors }}: Показывает ошибки валидации, если они есть.
        Аналогично создаются поля для описания и категории задачи:


- Запуск приложения в терминале на порту 8000
    python manage.py runserver 8000
- Приложение будет доступно по адресу http://127.0.0.1:8000/
- Админ-панель будет доступна по адресу http://127.0.0.1:8000/admin/


- Основные команды
    pip install django
    django-admin startproject todo_project
    python manage.py startapp tasks
    python manage.py runserver 8000
    python manage.py makemigrations tasks
    python manage.py migrate
    python manage.py createsuperuser

