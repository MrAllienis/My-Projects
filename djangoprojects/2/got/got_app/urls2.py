from django.urls import path, include
from .views import CharacterViewSet


urlpatterns = [
    path('', CharacterViewSet.show_all),

]
