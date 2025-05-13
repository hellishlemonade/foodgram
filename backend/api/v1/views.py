from djoser.views import UserViewSet
from rest_framework.response import Response
from django.contrib.auth import get_user_model


User = get_user_model()


class MyUserViewSet(UserViewSet):
    lookup_field = 'id'
