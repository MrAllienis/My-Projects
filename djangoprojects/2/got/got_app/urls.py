from django.urls import path, include
from rest_framework import routers
from .views import CharacterViewSet

router = routers.DefaultRouter()

router.register('got_app', CharacterViewSet)



urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls'))

]
