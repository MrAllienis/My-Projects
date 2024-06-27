from django.shortcuts import render
from .models import Character
from .serializers import CharacterSerializer
from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from .permissions import AllForAdminOtherReadOnly
from rest_framework import filters


# Create your views here.
class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer
    permission_classes = (AllForAdminOtherReadOnly, )
    filter_backends = [filters.OrderingFilter]
    search_fields = ['house_name']

    def show_all(request):
        characters = Character.objects.all().order_by('status')
        return render(
            request,
            'got_app\show_all.html',
            {'char': characters},
        )
